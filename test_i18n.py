import i18n
from core import CompatLayer

def test_lang(lang_code):
    print(f"--- Testing Language: {lang_code} ---")
    i18n.set_language(lang_code)
    compat = CompatLayer()
    
    # Test 1: File Not Found Error
    print(f"ls non_existent: {compat.ls('non_existent')}")
    
    # Test 2: Success Message (mkdir)
    print(f"mkdir test_dir: {compat.mkdir('test_dir_' + lang_code)}")
    
    # Clean up
    compat.rm('test_dir_' + lang_code, recursive=True)
    print()

if __name__ == "__main__":
    test_lang('en')
    test_lang('zh')
    test_lang('fr')
    test_lang('ja')
    test_lang('ru')
