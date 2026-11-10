from __future__ import annotations

from typing import Any


def calculate_cbm(
    length_cm: float | int | str,
    width_cm: float | int | str,
    height_cm: float | int | str,
    weight_kg: float | int | str = 0.0,
    quantity: int | str = 1,
) -> dict[str, Any]:
    """Calculate CBM, volumetric weight, and chargeable shipping weight for cargo packages."""
    try:
        length = float(length_cm)
        width = float(width_cm)
        height = float(height_cm)
        weight = float(weight_kg)
        qty = int(quantity)
    except (ValueError, TypeError):
        return {
            "status": "error",
            "message": "Kích thước (dài, rộng, cao), trọng lượng hoặc số lượng phải là giá trị số hợp lệ.",
        }

    if length <= 0 or width <= 0 or height <= 0:
        return {
            "status": "error",
            "message": "Kích thước chiều dài, chiều rộng và chiều cao phải lớn hơn 0.",
        }

    if qty <= 0:
        return {
            "status": "error",
            "message": "Số lượng kiện hàng phải lớn hơn 0.",
        }

    if weight < 0:
        return {
            "status": "error",
            "message": "Trọng lượng thực tế không được là số âm.",
        }

    # CBM calculation: (L * W * H in cm) / 1,000,000
    cbm_per_item = (length * width * height) / 1_000_000.0
    total_cbm = cbm_per_item * qty

    # Volumetric weight (Air freight standard divisor = 5000): (L * W * H in cm) / 5000
    vol_weight_per_item = (length * width * height) / 5000.0
    total_vol_weight = vol_weight_per_item * qty

    total_actual_weight = weight * qty
    chargeable_weight = max(total_actual_weight, total_vol_weight)

    return {
        "status": "success",
        "cbm_per_item": round(cbm_per_item, 6),
        "total_cbm": round(total_cbm, 4),
        "actual_weight_kg": round(total_actual_weight, 2),
        "volumetric_weight_kg": round(total_vol_weight, 2),
        "chargeable_weight_kg": round(chargeable_weight, 2),
        "quantity": qty,
        "summary": (
            f"Tổng thể tích: {total_cbm:.4f} CBM | "
            f"Trọng lượng thực tế: {total_actual_weight:.2f} kg | "
            f"Trọng lượng thể tích: {total_vol_weight:.2f} kg | "
            f"Trọng lượng tính cước: {chargeable_weight:.2f} kg cho {qty} kiện hàng ({length}x{width}x{height} cm)."
        ),
    }
