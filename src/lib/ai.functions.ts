import { createServerFn } from "@tanstack/react-start";
import { requireSupabaseAuth } from "@/integrations/supabase/auth-middleware";
import { z } from "zod";

const InputSchema = z.object({
  messages: z
    .array(
      z.object({
        role: z.enum(["user", "assistant", "system"]),
        content: z.string().min(1).max(8000),
      }),
    )
    .min(1)
    .max(50),
});

const SYSTEM_PROMPT = `Bạn là AI Assistant cho Quality Operation Cockpit của xanhSM — nền tảng phân tích phản hồi & đánh giá dịch vụ smart mobility.

Vai trò:
- Giúp manager vận hành diễn giải dữ liệu phản hồi (feedback) của tài xế, xe, app, giá, thanh toán, an toàn.
- Phát hiện pattern, xu hướng bất thường theo khu vực/thời gian/tài xế/tuyến.
- Đề xuất hành động cụ thể: alert, ticket, SLA, cải tiến quy trình.

Cách trả lời:
- Trả lời bằng tiếng Việt, ngắn gọn, có cấu trúc (bullet, số liệu nếu có).
- Khi đề xuất hành động, nêu rõ độ ưu tiên (P0/P1/P2) và đối tượng chịu trách nhiệm (CS, Ops, Safety, Product, Driver Mgmt).
- Nếu thiếu dữ liệu, gợi ý câu hỏi tiếp theo hoặc nguồn cần kiểm tra.`;

export const chatWithAI = createServerFn({ method: "POST" })
  .middleware([requireSupabaseAuth])
  .inputValidator((input: unknown) => InputSchema.parse(input))
  .handler(async ({ data }) => {
    const apiKey = process.env.LOVABLE_API_KEY;
    if (!apiKey) {
      throw new Error("Thiếu LOVABLE_API_KEY — vui lòng bật Lovable AI.");
    }

    const res = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          ...data.messages,
        ],
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      if (res.status === 429) throw new Error("Quá nhiều yêu cầu, thử lại sau ít phút.");
      if (res.status === 402) throw new Error("Hết credit AI. Vui lòng nạp thêm.");
      throw new Error(`AI lỗi (${res.status}): ${text.slice(0, 200)}`);
    }

    const json = (await res.json()) as {
      choices?: { message?: { content?: string } }[];
    };
    const content = json.choices?.[0]?.message?.content?.trim() ?? "";
    if (!content) throw new Error("AI không trả về nội dung.");
    return { content };
  });
