def get_frequency_map(word):
    freq = {}
    for char in word:
        if char.isalpha():
            freq[char] = freq.get(char, 0) + 1
    return freq

def convert_txt_to_js(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        words = [line.strip().strip('"') for line in f if line.strip()]

    js_lines = ['export const words = {']
    for word in words:
        freq_map = get_frequency_map(word)
        # Create a JS object string from the freq_map
        freq_str = ', '.join(f"'{k}': {v}" for k, v in freq_map.items())
        js_lines.append(f"  '{word}': {{{freq_str}}},")
    js_lines.append('};')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(js_lines))

# Example usage
convert_txt_to_js('wordlist_filtered.txt', 'words.js')