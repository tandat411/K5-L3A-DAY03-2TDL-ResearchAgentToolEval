---
name: cbm_calculator
track: bonus
kind: local_formatter
provider: Local
requires_env: []
inputs: [length_cm, width_cm, height_cm, weight_kg, quantity]
outputs: [status, cbm_per_item, total_cbm, actual_weight_kg, volumetric_weight_kg, chargeable_weight_kg, summary]
side_effect: false
---
# cbm_calculator

Tính toán thể tích đóng gói (CBM - Cubic Meters) và trọng lượng quy đổi thể tích (Volumetric Weight) cho hàng hóa thủ công mỹ nghệ xuất khẩu.
Hỗ trợ xác định trọng lượng tính cước (Chargeable Weight) theo chuẩn vận tải quốc tế (hàng không và đường biển).
