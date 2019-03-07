import codecs

# The pipes have ears (and many states have root certs in your browser)
def deobfuscate(interesting_string_that_is_obfuscated):
    return codecs.encode(interesting_string_that_is_obfuscated, encoding='rot13')
