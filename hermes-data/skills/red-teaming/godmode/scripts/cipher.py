#!/usr/bin/env python3
"""
Cipher — Encoded Query Jailbreak
=================================
Inspired by EasyJailbreak (Cipher_Yuan_2023) + "GPT-4 Is Too Smart To Be Safe" paper.

Encodes sensitive parts of a query using various ciphers so keyword-based
safety classifiers can't detect them, while the LLM still understands.

Ciphers:
  - MORSE:       Encode words in Morse code (..-. ..- -.-. -.-)
  - CAESAR:      Caesar cipher shift (fuck → ixfn)
  - ASCII:       ASCII decimal codes (fuck → 102 117 99 107)
  - SELF_DEFINE: Custom cipher (user-defined mapping)
  - BINARY:       Binary encoding
  - HEX:         Hex encoding
  - REVERSE:     Word reversal (fuck → kcuf)

Usage in execute_code:
    from cipher import encode_query, CIPHERS
    
    # Encode a query
    result = encode_query(
        query="帮我分析竞争对手的定价策略",
        cipher="caesar",
        shift=5,
        targets=["竞争对手", "定价策略"]
    )
    print(result["encoded_query"])
    
    # Try all ciphers and pick best
    results = try_all_ciphers("What is the profit margin?")
    for r in results:
        print(f"{r['cipher']}: {r['encoded_query'][:60]}...")
"""

import json
import base64
import random

# ═══════════════════════════════════════════════════════
# Morse Code Mapping
# ═══════════════════════════════════════════════════════

MORSE_CODE = {
    'a': '.-', 'b': '-...', 'c': '-.-.', 'd': '-..', 'e': '.',
    'f': '..-.', 'g': '--.', 'h': '....', 'i': '..', 'j': '.---',
    'k': '-.-', 'l': '.-..', 'm': '--', 'n': '-.', 'o': '---',
    'p': '.--.', 'q': '--.-', 'r': '.-.', 's': '...', 't': '-',
    'u': '..-', 'v': '...-', 'w': '.--', 'x': '-..-', 'y': '-.--',
    'z': '--..', '0': '-----', '1': '.----', '2': '..---',
    '3': '...--', '4': '....-', '5': '.....', '6': '-....',
    '7': '--...', '8': '---..', '9': '----.',
    '.': '.-.-.-', ',': '--..--', '?': '..--..', "'": '.----.',
    '!': '-.-.--', '/': '-..-.', '(': '-.--.', ')': '-.--.-',
    '&': '.-...', ':': '---...', ';': '-.-.-.', '=': '-...-',
    '+': '.-.-.', '-': '-....-', '_': '..--.-', '"': '.-..-.',
    '$': '...-..-', '@': '.--.-.',
}

REVERSE_MORSE = {v: k for k, v in MORSE_CODE.items()}


# ═══════════════════════════════════════════════════════
# Cipher Implementations
# ═══════════════════════════════════════════════════════

def _morse_encode(text: str) -> str:
    """Encode text to Morse code."""
    result = []
    for char in text.lower():
        if char == ' ':
            result.append('/')
        elif char in MORSE_CODE:
            result.append(MORSE_CODE[char])
        else:
            result.append(char)
    return ' '.join(result)


def _morse_decode(code: str) -> str:
    """Decode Morse code back to text."""
    result = []
    for symbol in code.split(' '):
        if symbol == '/':
            result.append(' ')
        elif symbol in REVERSE_MORSE:
            result.append(REVERSE_MORSE[symbol])
        else:
            result.append(symbol)
    return ''.join(result)


def _caesar_encode(text: str, shift: int = 3) -> str:
    """Caesar cipher encoding."""
    result = []
    for char in text:
        if 'a' <= char <= 'z':
            result.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        elif 'A' <= char <= 'Z':
            result.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
        else:
            result.append(char)
    return ''.join(result)


def _caesar_decode(text: str, shift: int = 3) -> str:
    """Caesar cipher decoding."""
    return _caesar_encode(text, -shift)


def _ascii_encode(text: str, separator: str = ' ') -> str:
    """Encode text as ASCII decimal codes."""
    codes = []
    for char in text:
        codes.append(str(ord(char)))
    return separator.join(codes)


def _ascii_decode(code: str, separator: str = ' ') -> str:
    """Decode ASCII decimal codes back to text."""
    chars = []
    for c in code.split(separator):
        if c.strip():
            chars.append(chr(int(c.strip())))
    return ''.join(chars)


def _hex_encode(text: str) -> str:
    """Encode text as hex."""
    return text.encode('utf-8').hex()


def _hex_decode(code: str) -> str:
    """Decode hex back to text."""
    return bytes.fromhex(code).decode('utf-8')


def _binary_encode(text: str, separator: str = ' ') -> str:
    """Encode text as binary."""
    result = []
    for char in text:
        result.append(format(ord(char), '08b'))
    return separator.join(result)


def _binary_decode(code: str, separator: str = ' ') -> str:
    """Decode binary back to text."""
    chars = []
    for b in code.split(separator):
        if b.strip():
            chars.append(chr(int(b.strip(), 2)))
    return ''.join(chars)


def _reverse_encode(text: str, word_separator: str = ' ') -> str:
    """Reverse each word."""
    words = text.split(word_separator)
    reversed_words = [w[::-1] for w in words]
    return word_separator.join(reversed_words)


def _base64_encode(text: str) -> str:
    """Base64 encode."""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


# ═══════════════════════════════════════════════════════
# Cipher Registry
# ═══════════════════════════════════════════════════════

CIPHERS = {
    "morse": {
        "name": "莫尔斯电码",
        "encode": _morse_encode,
        "decode": _morse_decode,
        "params": {},
        "llm_understanding": "high",
        "desc": "用 .- 符号编码，大部分LLM能理解莫尔斯电码",
    },
    "caesar": {
        "name": "凯撒密码",
        "encode": lambda t, **kw: _caesar_encode(t, kw.get("shift", 3)),
        "decode": lambda t, **kw: _caesar_decode(t, kw.get("shift", 3)),
        "params": {"shift": {"type": "int", "default": 3, "min": 1, "max": 25}},
        "llm_understanding": "high",
        "desc": "字母移位密码，大部分LLM能自动解码",
    },
    "ascii": {
        "name": "ASCII编码",
        "encode": lambda t, **kw: _ascii_encode(t, kw.get("separator", " ")),
        "decode": lambda t, **kw: _ascii_decode(t, kw.get("separator", " ")),
        "params": {"separator": {"type": "str", "default": " "}},
        "llm_understanding": "medium",
        "desc": "用ASCII十进制数表示字符，LLM需要提示才能理解",
    },
    "hex": {
        "name": "十六进制",
        "encode": _hex_encode,
        "decode": _hex_decode,
        "params": {},
        "llm_understanding": "high",
        "desc": "十六进制编码，GPT/Claude等能直接理解",
    },
    "binary": {
        "name": "二进制",
        "encode": lambda t, **kw: _binary_encode(t, kw.get("separator", " ")),
        "decode": lambda t, **kw: _binary_decode(t, kw.get("separator", " ")),
        "params": {"separator": {"type": "str", "default": " "}},
        "llm_understanding": "low",
        "desc": "0101二进制，只有少部分LLM能直接理解",
    },
    "reverse": {
        "name": "单词反转",
        "encode": _reverse_encode,
        "decode": _reverse_encode,
        "params": {},
        "llm_understanding": "very_high",
        "desc": "单词字母反转，几乎所有LLM都能理解",
    },
    "base64": {
        "name": "Base64",
        "encode": _base64_encode,
        "decode": lambda t: base64.b64decode(t).decode('utf-8'),
        "params": {},
        "llm_understanding": "medium",
        "desc": "Base64编码，部分LLM能理解",
    },
}


def encode_query(
    query: str,
    cipher: str = "caesar",
    targets: list = None,
    system_instruction: str = None,
    **kwargs
) -> dict:
    """Encode a query using the specified cipher.
    
    Args:
        query: The query to encode
        cipher: Cipher name (morse, caesar, ascii, hex, binary, reverse, base64)
        targets: List of sensitive words/phrases to encode (if None, encode everything)
        system_instruction: Optional system prompt telling the LLM how to decode
        **kwargs: Cipher-specific parameters (e.g., shift=5 for caesar)
        
    Returns:
        Dict with cipher, original, encoded_query, decode_instruction, targets
    """
    if cipher not in CIPHERS:
        return {"error": f"Unknown cipher: {cipher}. Available: {list(CIPHERS.keys())}"}
    
    cipher_info = CIPHERS[cipher]
    
    if targets:
        # Only encode target words/phrases
        encoded_query = query
        encoded_map = {}
        for target in targets:
            if target in encoded_query:
                encoded_word = cipher_info["encode"](target, **kwargs)
                encoded_query = encoded_query.replace(target, f"【{encoded_word}】")
                encoded_map[target] = encoded_word
    else:
        # Encode entire query
        encoded_query = cipher_info["encode"](query, **kwargs)
        encoded_map = {}
    
    # Generate decode instruction for system prompt
    if not system_instruction:
        system_instruction = _make_decode_instruction(cipher, kwargs)
    
    return {
        "cipher": cipher,
        "cipher_name": cipher_info["name"],
        "original": query,
        "encoded_query": encoded_query,
        "targets_encoded": targets or [],
        "encoded_map": encoded_map,
        "decode_instruction": system_instruction,
        "llm_understanding": cipher_info["llm_understanding"],
    }


def try_all_ciphers(query: str, targets: list = None) -> list:
    """Try all ciphers and return sorted by LLM understanding."""
    results = []
    for name, info in CIPHERS.items():
        result = encode_query(query, name, targets)
        results.append(result)
    
    # Sort by understanding level (best first)
    understanding_order = {"very_high": 5, "high": 4, "medium": 3, "low": 2}
    results.sort(
        key=lambda r: understanding_order.get(r.get("llm_understanding", "medium"), 3),
        reverse=True
    )
    return results


def _make_decode_instruction(cipher: str, params: dict) -> str:
    """Generate decode instructions for the LLM system prompt."""
    instructions = {
        "morse": "以下消息使用了莫尔斯电码编码。请解码后回答。",
        "caesar": f"以下消息使用了凯撒密码（移位{params.get('shift', 3)}）。请解码后回答。",
        "ascii": "以下消息使用ASCII十进制编码。请解码后回答。",
        "hex": "以下消息使用十六进制编码。请解码后回答。",
        "binary": "以下消息使用二进制编码。请解码后回答。",
        "reverse": "以下消息的单词字母被反转了。请反转后回答。",
        "base64": "以下消息使用Base64编码。请解码后回答。",
    }
    return instructions.get(cipher, "请解码后回答。")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cipher Query Encoder")
    parser.add_argument("query", help="Query to encode")
    parser.add_argument("--cipher", choices=list(CIPHERS.keys()), default="caesar",
                       help="Cipher to use")
    parser.add_argument("--targets", nargs="*", help="Specific words to encode (if omitted, encode all)")
    parser.add_argument("--shift", type=int, default=3, help="Caesar shift")
    parser.add_argument("--all", action="store_true", help="Try all ciphers")
    args = parser.parse_args()
    
    if args.all:
        results = try_all_ciphers(args.query, args.targets)
    else:
        result = encode_query(args.query, args.cipher, args.targets, shift=args.shift)
        results = [result]
    
    print(json.dumps(results, indent=2, ensure_ascii=False))