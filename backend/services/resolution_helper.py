def snap_to_multiple_of_32(val: int) -> int:
    return max(32, (val // 32) * 32)


def get_model_valid_dimensions(resolution: str = "512p", aspect_ratio: str = "16:9") -> tuple[int, int]:
    # Standard baseline resolutions (all exact multiples of 32)
    mapping = {
        "512p": {
            "16:9": (704, 384),
            "9:16": (384, 704),
            "1:1": (512, 512),
            "4:5": (448, 576),
        },
        "720p": {
            "16:9": (1280, 736),
            "9:16": (736, 1280),
            "1:1": (704, 704),
            "4:5": (640, 800),
        },
        "1080p": {
            "16:9": (1920, 1088),
            "9:16": (1088, 1920),
            "1:1": (1024, 1024),
            "4:5": (800, 1024),
        }
    }

    res_map = mapping.get(resolution, mapping["512p"])
    w, h = res_map.get(aspect_ratio, (704, 384))
    return snap_to_multiple_of_32(w), snap_to_multiple_of_32(h)
