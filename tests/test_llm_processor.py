import sys
import os

if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Add src to python path to make importing clean
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.llm_processor import apply_linkedin_company_tags

def test_company_tagging():
    print("Testing LinkedIn Company Tagging...")
    
    # 1. Test normal case replacement
    text_1 = "Microsoft enabled Anthropic Claude 5.6 in their 365 app, competing with OpenAI."
    expected_1 = "@[Microsoft](urn:li:organization:1035) enabled @[Anthropic](urn:li:organization:7936402) Claude 5.6 in their 365 app, competing with @[OpenAI](urn:li:organization:11130470)."
    result_1 = apply_linkedin_company_tags(text_1)
    
    assert result_1 == expected_1, f"Failed normal replacement.\nGot: {result_1}\nExpected: {expected_1}"
    print("✅ Normal replacement passed.")
    
    # 2. Test case-insensitivity
    text_2 = "microsoft and openai compete with nvidia."
    expected_2 = "@[Microsoft](urn:li:organization:1035) and @[OpenAI](urn:li:organization:11130470) compete with @[NVIDIA](urn:li:organization:3608)."
    result_2 = apply_linkedin_company_tags(text_2)
    assert result_2 == expected_2, f"Failed case-insensitive replacement.\nGot: {result_2}\nExpected: {expected_2}"
    print("✅ Case-insensitive replacement passed.")
    
    # 3. Test hashtag avoidance
    text_3 = "Check out the latest from #OpenAI and #Microsoft! Microsoft is leading."
    expected_3 = "Check out the latest from #OpenAI and #Microsoft! @[Microsoft](urn:li:organization:1035) is leading."
    result_3 = apply_linkedin_company_tags(text_3)
    assert result_3 == expected_3, f"Failed hashtag avoidance.\nGot: {result_3}\nExpected: {expected_3}"
    print("✅ Hashtag avoidance passed.")
    
    # 4. Test other companies in mapping
    text_4 = "Meta, Google, Cohere, Mistral AI, Perplexity AI, Midjourney, and xAI are all in the list."
    expected_4 = "@[Meta](urn:li:organization:10667), @[Google](urn:li:organization:1441), @[Cohere](urn:li:organization:24024765), @[Mistral AI](urn:li:organization:94273421), @[Perplexity](urn:li:organization:88007673), @[Midjourney](urn:li:organization:82318617), and @[xAI](urn:li:organization:5191206) are all in the list."
    result_4 = apply_linkedin_company_tags(text_4)
    assert result_4 == expected_4, f"Failed other companies replacement.\nGot: {result_4}\nExpected: {expected_4}"
    print("✅ All tech brand mappings passed.")
    
    # 5. Test URL protection
    text_5 = "Sources:\nhttps://openai.com/index/deutsche-telekom\nhttps://google.com/search"
    expected_5 = "Sources:\nhttps://openai.com/index/deutsche-telekom\nhttps://google.com/search"
    result_5 = apply_linkedin_company_tags(text_5)
    assert result_5 == expected_5, f"Failed URL protection. URL got modified!\nGot: {result_5}\nExpected: {expected_5}"
    print("✅ URL protection passed.")

if __name__ == "__main__":
    test_company_tagging()
    print("All tests passed successfully!")
