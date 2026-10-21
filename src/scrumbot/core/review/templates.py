"""The description templates of the Sprint Tech process (bot spec §7.3, D65, A106), and the blocking item the AI's
check gives. The points are those of `rule.html` §1.3 as written, without the `Tài liệu: …` point of each template:
documents may come later in the process. Pure."""

from __future__ import annotations

from dataclasses import replace

from scrumbot.core.model import ORDER_KINDS, OrderKind
from scrumbot.core.outcome import AiReview, ReviewItem

OTHER = "other"  # the AI's type for an order outside the 8, e.g. a new app, which follows its own SRS

TEMPLATES: dict[OrderKind, tuple[str, ...]] = {
    OrderKind.ADS: (
        "Sửa thì ghi Hiện trạng và Mong muốn của từng vị trí",
        "Danh sách vị trí quảng cáo: màn hình, thời điểm hiển thị",
        "Mỗi vị trí: định dạng, mạng QC, ad unit ID, config name trên Remote Config, timeout",
        "Luồng hiển thị (link Flow), tần suất, preload",
        "Nghiệm thu khi: từng vị trí hiện đúng định dạng, đúng thời điểm, bật/tắt được bằng config",
    ),
    OrderKind.IAP: (
        "Danh sách gói: product ID, loại (subscription / mua một lần), chu kỳ, trial",
        "Paywall: màn nào, điều kiện hiển thị",
        "Remote Config: key, giá trị mặc định",
        "Event tracking IAP cần bắn",
        "Nghiệm thu khi: mua thử sandbox, khôi phục, hủy, hết hạn đều đúng",
    ),
    OrderKind.TRACKING: (
        "Danh sách event theo từng màn",
        "Mỗi event: tên, parameter/value, thời điểm bắn",
        "Ảnh màn hình đánh dấu vị trí bắn",
        "Nơi nhận: Firebase, AppsFlyer…",
        "Nghiệm thu khi: event hiện đúng tên, đúng param trên DebugView",
    ),
    OrderKind.FEATURE: (
        "Mục tiêu và lý do, kèm số liệu nếu có",
        "Hiện trạng",
        "Mong muốn: luồng từng bước, màn hình, điều kiện",
        "Remote Config bật/tắt: key, giá trị mặc định",
        "Ngoài phạm vi",
        "Nghiệm thu khi: điều kiện kiểm tra được",
    ),
    OrderKind.BUGFIX: (
        "Tên lỗi, mã lỗi và link lỗi cho từng lỗi",
        "Version app, build; thiết bị, OS nếu biết",
        "Bước tái hiện, kết quả thực tế và mong đợi",
        "Ảnh, video hoặc log (nếu có)",
    ),
    OrderKind.POLICY: (
        "Lý do bị từ chối, copy nguyên văn, kèm email hoặc ảnh Play Console",
        "Hạn store yêu cầu (nếu có)",
        "Danh sách hành động, mỗi hành động có Hiện trạng và Mong muốn",
        "Nội dung chữ thay đổi ghi nguyên văn",
        "Nghiệm thu khi: build đã sửa đủ mọi hành động, sẵn sàng nộp lại",
    ),
    OrderKind.RESEARCH: (
        "Câu hỏi cần trả lời và vì sao",
        "Input: dữ liệu, tài liệu, app tham khảo (đính kèm)",
        "Output mong muốn và định dạng",
        "Giới hạn: timebox, những gì không làm",
        "Nghiệm thu khi: điều kiện để coi là xong",
    ),
    OrderKind.INFRA: (
        "Hiện trạng: đang dùng tài khoản, project, SDK nào",
        "Đích: chuyển sang đâu, phiên bản nào",
        "Danh sách việc: Remote Config, Firebase, keystore, ad unit, IAP…",
        "Lý do và hạn (ví dụ hạn target API của Google)",
        "Nghiệm thu khi: app chạy trên đích mới, config và dữ liệu đúng",
    ),
}


def settled(declared: OrderKind | None, ai: AiReview) -> AiReview:
    """The AI's answer with the type the review uses: the file's `Loại đơn` wins over the AI's (A107). The check
    counts only for one of the 8 types."""
    kind = declared or _kind(ai.kind)
    if kind is None:
        return replace(ai, checked=False)
    return replace(ai, kind=kind.value)


def template_item(ai: AiReview) -> ReviewItem | None:
    """`REVIEW-TEMPLATE` for the points the AI names, in the words and the order of the template; a number outside
    the template is ignored, so no text of the AI reaches the message. `ai` is `settled`."""
    kind = _kind(ai.kind)
    if kind is None or not ai.checked:
        return None
    points = TEMPLATES[kind]
    missing = [points[number - 1] for number in sorted(set(ai.missing)) if 1 <= number <= len(points)]
    if not missing:
        return None
    label = ORDER_KINDS[kind]
    return ReviewItem("REVIEW-TEMPLATE", f"Mô tả chưa đủ ý của mẫu {label} (AI chấm): {'; '.join(missing)}.")


def _kind(value: str) -> OrderKind | None:
    try:
        return OrderKind(value)
    except ValueError:
        return None
