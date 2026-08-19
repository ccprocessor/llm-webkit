from urllib.parse import urlparse

import xxhash


# 定义计算domain_hash_id的UDF
def compute_domain_hash(domain, hash_count) -> int:
    if domain is None:
        return None
    return xxhash.xxh64_intdigest(domain.encode('utf-8')) % hash_count


# 定义提取domain的UDF
def extract_domain(url):
    if url is None:
        return None
    try:
        hostname = urlparse(url).hostname
        return hostname.lower() if hostname else None
    except Exception as e:
        print(f"提取domain失败: {e}")
        return None
