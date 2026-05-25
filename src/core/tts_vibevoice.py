import os
import sys
import time
import torch
import copy
from typing import Optional

# Add the VibeVoice-main repo to sys.path so we can import its modules
repo_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'VibeVoice-main')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

try:
    from vibevoice.modular.modeling_vibevoice_streaming_inference import VibeVoiceStreamingForConditionalGenerationInference
    from vibevoice.processor.vibevoice_streaming_processor import VibeVoiceStreamingProcessor
    from demo.realtime_model_inference_from_file import VoiceMapper
    from transformers.cache_utils import DynamicCache
    from transformers.modeling_outputs import BaseModelOutputWithPast
    VIBEVOICE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import VibeVoice modules. Please ensure VibeVoice-main is set up. Error: {e}")
    VIBEVOICE_AVAILABLE = False


class VibeVoiceEngine:
    def __init__(self, model_path="microsoft/VibeVoice-Realtime-0.5B", speaker_name="Carter"):
        """
        Initializes the VibeVoice model once so it can be reused for multiple slides quickly.
        """
        if not VIBEVOICE_AVAILABLE:
            raise ImportError("VibeVoice is not available. Please install dependencies.")
            
        self.model_path = model_path
        self.speaker_name = speaker_name
        self.device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        print(f"[VibeVoice] Initializing engine on device: {self.device}")
        
        self.voice_mapper = VoiceMapper()
        self.processor = VibeVoiceStreamingProcessor.from_pretrained(model_path)
        
        # Determine dtype and attention implementation
        if self.device == "mps":
            load_dtype = torch.float32
            attn_impl = "sdpa"
        elif self.device == "cuda":
            load_dtype = torch.bfloat16
            attn_impl = "flash_attention_2"
        else: # cpu
            load_dtype = torch.float32
            attn_impl = "sdpa"
            
        try:
            self.model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                model_path,
                torch_dtype=load_dtype,
                device_map=self.device if self.device in ("cuda", "cpu") else None,
                attn_implementation=attn_impl,
            )
            if self.device == "mps":
                self.model.to("mps")
        except Exception as e:
            if attn_impl == 'flash_attention_2':
                print("[VibeVoice] flash_attention_2 failed, falling back to sdpa...")
                self.model = VibeVoiceStreamingForConditionalGenerationInference.from_pretrained(
                    model_path,
                    torch_dtype=load_dtype,
                    device_map=self.device if self.device in ("cuda", "cpu") else None,
                    attn_implementation='sdpa'
                )
                if self.device == "mps":
                    self.model.to("mps")
            else:
                raise e

        self.model.eval()
        self.model.set_ddpm_inference_steps(num_steps=5)
        
        # Pre-load the voice preset
        voice_sample = self.voice_mapper.get_voice_path(self.speaker_name)
        with torch.serialization.safe_globals([BaseModelOutputWithPast, DynamicCache]):
            self.cached_prompt = torch.load(voice_sample, map_location=self.device, weights_only=True)
            
        print("[VibeVoice] Initialization complete.")

    def generate_audio(self, text: str, output_path: str) -> Optional[str]:
        """
        Generates audio for the given text and saves it to output_path.
        Returns the output_path on success, or None on failure.
        """
        text = text.replace("’", "'").replace('“', '"').replace('”', '"')
        
        inputs = self.processor.process_input_with_cached_prompt(
            text=text,
            cached_prompt=self.cached_prompt,
            padding=True,
            return_tensors="pt",
            return_attention_mask=True,
        )
        
        # Move tensors to device
        for k, v in inputs.items():
            if torch.is_tensor(v):
                inputs[k] = v.to(self.device)
                
        print(f"[VibeVoice] Generating audio for text ({len(text)} chars)...")
        start_time = time.time()
        
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=None,
            cfg_scale=1.5,
            tokenizer=self.processor.tokenizer,
            generation_config={'do_sample': False},
            verbose=False,
            all_prefilled_outputs=copy.deepcopy(self.cached_prompt),
        )
        
        if not outputs.speech_outputs or outputs.speech_outputs[0] is None:
            print("[VibeVoice] Error: No audio output generated.")
            return None
            
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        self.processor.save_audio(outputs.speech_outputs[0], output_path=output_path)
        
        elapsed = time.time() - start_time
        print(f"[VibeVoice] Saved audio to {output_path} (Took {elapsed:.1f}s)")
        
        return output_path

if __name__ == "__main__":
    # Test generation
    engine = VibeVoiceEngine(speaker_name="Carter")
    engine.generate_audio(
        "Welcome to Gen A.I. Pro. Here is the latest breaking news.", 
        "drafts/test_vibevoice_class.wav"
    )
