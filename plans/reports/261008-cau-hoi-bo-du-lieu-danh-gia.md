# Câu hỏi: bộ dữ liệu đánh giá 5 case

Ngày 2026-10-08. Mục tiêu: tạo 5 bộ input cho tool, chạy tool, chấm output so với đáp án, rồi cải thiện tool theo
kết quả chấm.

**Cách trả lời**

- Đánh `x` vào ô bạn chọn: `- [x]`.
- **Để trống cả câu nghĩa là đồng ý với phương án có ghi "(đề xuất)".** Chỉ cần điền chỗ không đồng ý hoặc cần nói thêm.
- Với bảng, mỗi dòng chọn một ô `Đồng ý` / `Không đồng ý`; không đồng ý thì ghi lý do hoặc phương án khác vào cột ghi chú.
- Ghi chú thêm thì viết vào dòng `Trả lời:` của câu đó.

Sau khi bạn trả lời, mình ghi quyết định vào `confirm.md` (D/A/O) rồi mới tạo dữ liệu.

> **Kết quả (2026-10-08):** user không có câu trả lời và giao Claude quyết định toàn bộ. Claude chọn mọi phương án
> "(đề xuất)", trừ A3: không có TM để điền đáp án cho case giả lập, nên case giả lập chỉ chấm theo spec (O10).
> Ghi vào `confirm.md` thành A35–A42 và O10.

---

## Hiện trạng: backtest đã đo gì, chưa đo gì

- 154 test pass. Code luật TM (D28–D35) **chưa commit** (15 file sửa, 5 file mới), xem câu E2.
- Backtest hiện tại (`--backtest`): tool khớp TM **43/92 đơn (47%)**. Backtest **không đo được** bốn thứ, vì file
  Tech manager không có dữ liệu cho chúng:

| Chưa đo được | Vì sao |
|---|---|
| Độ lớn do AI ước lượng | Export Tech manager không có `Mô tả`; backtest coi mọi đơn là M (A29). |
| Việc dở sprint trước | Trạng thái trong export là trạng thái hôm nay, không phải lúc sprint bắt đầu (A29). |
| Ngày nghỉ, dev `Nhận việc` = `N` | `devs.xlsx` không lưu ngày nghỉ của sprint cũ. |
| Luật TM, dữ liệu bẩn | Chưa có file luật thật nào; dữ liệu mẫu sạch (lần chạy E không có cảnh báo nào). |

Bộ 5 case nên lấp đúng các chỗ này. Dữ liệu thật dùng được làm đáp án nằm trong
`input/Maintain_update_Sprint_10_va_9.xlsx`:

| Sheet | Đơn gốc | Có tên dev trong danh sách | Có `Ước lượng (h)` | Có `Mô tả` | Hạng theo giờ thật S/M/L/XL (ranh giới ở câu C3) |
|---|---|---|---|---|---|
| Sprint 9 | 12 | 11 | 12 | 6 | 2 / 4 / 2 / 4 |
| Sprint 8 | 11 | 9 | 8 | 8 | 2 / 1 / 4 / 1 |
| Sprint 7 | 8 | 8 | 8 | 3 | 3 / 0 / 4 / 1 |
| Sprint 6 | 3 | 3 | 3 | 2 | 1 / 1 / 0 / 1 |
| Sprint 10 | 6 | 5 | (bỏ qua, D3) | 2 | — |

Sprint 9 là sprint tốt nhất để chấm độ lớn AI: 12/12 đơn có giờ thật, trải đủ 4 hạng (2h đến 83h).

---

## Phương án đề xuất (tóm tắt)

**2 case dựng lại từ sprint thật** (đáp án có sẵn: người TM đã giao và số giờ thật) **+ 3 case giả lập theo kịch
bản** (đáp án do TM điền trước khi chạy tool, cộng phần "tool phải làm gì theo spec" do mình tính tay). Mỗi case là
một thư mục input riêng, chạy bằng `assigntool --input eval/case-N-...`. Chi tiết từng case ở câu B2.

---

## A. Đánh giá cái gì, đáp án ở đâu

### A1. Chấm những gì?

Chọn nhiều ô được.

- [ ] **PIC so với lựa chọn của TM (đề xuất).** Như backtest: khớp khi PIC của tool là một trong các dev TM giao.
- [ ] **PIC so với spec (đề xuất).** Tool có làm đúng điều spec §7, §14 nói không (lỗi code), tách khỏi câu hỏi "luật
      có hợp lý không".
- [ ] **Độ lớn AI so với giờ thật (đề xuất).** Chỉ chấm được trên case dựng lại (có `Ước lượng (h)`).
- [ ] **Cảnh báo (đề xuất):** đúng, thiếu, thừa so với spec §9.
- [ ] **Độ ổn định (đề xuất):** chạy AI nhiều lần trên cùng input, độ lớn và PIC đổi bao nhiêu (D27).
- [ ] Cột `Lý do` đọc có hiểu không: TM chấm mỗi đơn 1–3 điểm. Tốn thời gian của TM, nên không đề xuất mặc định.

Trả lời:

### A2. Đáp án lấy từ đâu?

- [ ] **Case dựng lại: người TM đã giao và giờ thật trong file. Case giả lập: TM điền PIC mong muốn, cộng phần
      "theo spec" mình tính tay trước khi chạy tool (đề xuất).** Hai loại đáp án đo hai việc khác nhau: "theo spec"
      bắt lỗi code, "theo TM" đo luật có hợp lý không.
- [ ] Mọi case đều do TM điền, kể cả case dựng lại.
- [ ] Chỉ đáp án "theo spec" do mình tính. **Không đề xuất làm đáp án duy nhất:** chỉ chứng minh code khớp spec,
      không cho biết TM có đồng ý không.

Trả lời:

### A3. Ai điền đáp án "theo TM" cho 3 case giả lập, và điền lúc nào?

Khoảng **27 đơn** cần điền (case 3: 5 đơn trống, case 4: 10, case 5: 12). Mỗi đơn: PIC mong muốn và các dev chấp
nhận được.

- [ ] **TM thật điền, trước khi xem output của tool (đề xuất).** Điền "mù" để không bị output của tool dẫn dắt.
- [ ] Bạn điền thay TM, trước khi xem output.
- [ ] Điền sau khi xem output. Nhanh hơn, nhưng dễ thấy output "cũng hợp lý" và chấm dễ dãi.

Người điền: ____________

Trả lời:

---

## B. Dữ liệu của 5 case

### B1. Dữ liệu thật hay giả lập?

- [ ] **2 case dựng lại từ sprint thật + 3 case giả lập (đề xuất).** Case thật cho đáp án khách quan và chấm được
      độ lớn AI; case giả lập phủ việc dở, nghỉ phép, luật TM, dữ liệu bẩn mà dữ liệu thật không có.
- [ ] 5 case dựng lại từ Sprint 6–10. Không phải điền đáp án, nhưng không đo được luật TM, nghỉ phép, dữ liệu bẩn;
      Sprint 6 chỉ có 3 đơn.
- [ ] 5 case giả lập. Kiểm soát được hoàn toàn, nhưng mọi đáp án đều phải điền tay và không chấm được độ lớn AI.

Trả lời:

### B2. Năm case đề xuất

| # | Case | Dữ liệu | Kiểm tra | Đáp án | Đồng ý | Không đồng ý | Ghi chú |
|---|---|---|---|---|---|---|---|
| 1 | **Sprint 9 dựng lại** | 12 đơn thật kèm `Mô tả`; xoá `Người làm` của 11 đơn có dev trong danh sách (đơn nghiên cứu PS Remote của RnD giữ nguyên, như backtest); lịch sử = file Tech manager tính tới ngày 21/09/2026 (câu C1); việc dở theo câu C2. Cả 11 đơn được giao một lượt vào ngày đầu sprint. | PIC so với TM (backtest: 8/11); độ lớn AI so với giờ thật (2h–83h) | Người TM giao, giờ thật | [ ] | [ ] | |
| 2 | **Sprint 8 dựng lại** | 11 đơn thật, 9 có dev trong danh sách; lịch sử tính tới 04/09/2026; sheet Sprint 7 làm sprint trước (không ai còn việc dở). | Cân tải so với TM: TM giao LinhNV 6/9 đơn, backtest chỉ khớp 2/9 | Người TM giao, giờ thật của 8 đơn | [ ] | [ ] | |
| 3 | **Giữa sprint, nghỉ phép, việc dở** | Sprint 11 giả lập (19/10–30/10/2026), 10 đơn: 5 đã giao sẵn, 5 đơn BA vừa lên còn trống (có 1 đơn urgent app mới, 1 đơn high của app mà người quen app đang nghỉ). `devs.xlsx`: MinhNM nghỉ cả sprint, AnTD nghỉ 3 ngày. Sheet Sprint 10 giả lập có việc dở khác nhau cho từng dev. | Giữ đơn giao sẵn (D10), loại dev nghỉ cả sprint, việc dở, cân tải khi chạy giữa sprint (D2) | TM điền + theo spec | [ ] | [ ] | |
| 4 | **Luật TM** | Sprint 11 giả lập, 10 đơn, kèm `luat.md` đủ 4 loại luật lấy cảm hứng từ backtest (vd `Chỉ định LinhNV · AR Dog`: TM giao Linh 9/9 đơn AR Dog). Thêm các ca biên: luật hết hạn, luật cho dev đang nghỉ (`RULE-DEV-UNAVAILABLE`), luật loại hết ứng viên (`RULE-NO-CANDIDATE`), `Ưu tiên` cho dev đã chạm giới hạn cân tải (D32). | Mỗi loại luật tác động đúng §7, §14; `Lý do` ghi đúng dòng luật | TM điền + theo spec | [ ] | [ ] | |
| 5 | **Dữ liệu bẩn, app mới** | Sprint 11 giả lập, 12 đơn, không có sheet sprint trước. Thiếu `App Name`, `Ưu tiên` lạ (`gấp`), `Hạn` trước `Ngày tạo`, `Loại` lạ (`Bug`), tên dev dạng NFD và thừa khoảng trắng, một tên dev gõ sai (cái giá đã biết của D14), app viết khác lịch sử (`Speaker Cleaner`, `fakecal`), `Nhiều App`, mô tả 5.000+ ký tự nhiều link, 3 app mới có đơn urgent. | Mọi cảnh báo của §9 kích hoạt đúng; tool không crash; prompt AI không vượt 30.000 ký tự | Theo spec + TM điền PIC | [ ] | [ ] | |

Muốn đổi hoặc thêm kịch bản nào (vd AI lỗi giữa chừng, một dev `Nhận việc` = `N`, sprint chỉ có 1–2 đơn)?

Trả lời:

### B3. Lịch sử và sprint trước của 3 case giả lập

- [ ] **Lịch sử = file Tech manager thật, dùng nguyên vẹn; đơn giả lập dùng tên app có thật trong lịch sử (AR Dog,
      VPN, PS Remote, Game Emulator…) cộng vài app mới. Sheet sprint trước là sheet giả lập để việc dở của từng dev
      đúng như kịch bản cần (đề xuất).** "Quen app" khi đó có ý nghĩa thật, TM điền đáp án dễ hơn.
- [ ] Lịch sử giả lập nhỏ riêng cho mỗi case. Kiểm soát được hoàn toàn, nhưng TM khó điền vì không phải app thật.
- [ ] Dùng sheet Sprint 10 thật làm sprint trước. Trạng thái của nó là ngày 06/10, khi sprint vừa bắt đầu, nên việc
      dở rất cao: LinhNV 9 dòng, TiếnBV 4, AnTD 2, MinhNM 1.

Trả lời:

### B4. `Mô tả` của đơn giả lập (để AI ước lượng)

- [ ] **Mình viết mô tả tiếng Việt theo văn phong BA trong file thật (danh sách đầu việc, link store/Figma giả), trải
      đủ 4 hạng S/M/L/XL, và ghi "hạng mình nhắm tới" trong đáp án (đề xuất).** Chỉ để tham khảo, không chấm như
      giờ thật.
- [ ] Lấy lại mô tả thật của đơn cũ, đổi sang app khác.
- [ ] Không có mô tả, chỉ tiêu đề (như 6/12 đơn của Sprint 9).

Trả lời:

### B5. Các mặc định nhỏ

| # | Mặc định | Đồng ý | Không đồng ý | Ghi chú |
|---|---|---|---|---|
| a | Danh sách dev là 4 dev của D7, tên thật (tên dev là cấu hình, spec §4); mỗi case có `devs.xlsx` riêng để đổi ngày nghỉ, `Nhận việc`. | [ ] | [ ] | |
| b | Người ngoài danh sách (QA, RnD) trong case giả lập dùng **tên giả**, không chép tên người thật. Case dựng lại giữ nguyên file thật. | [ ] | [ ] | |
| c | File sprint giả lập có layout y hệt export thật: tiêu đề dòng 1–3, header dòng 5, subtask thụt lề `└`, footer công thức. | [ ] | [ ] | |
| d | Dữ liệu được sinh bằng một script (`eval/build_cases.py`) từ `input/` và kịch bản, để sinh lại được và review được như code; file `.xlsx` sinh ra vẫn được commit. | [ ] | [ ] | |
| e | Không có case nào cố tình làm tool dừng với exit 2 (level sai, luật mâu thuẫn): các lỗi input đó đã có unit test. | [ ] | [ ] | |

Trả lời:

---

## C. Cách chạy

### C1. Ngày chạy: thêm cờ `--today`?

Tool lấy "hôm nay" từ đồng hồ máy cho hai việc: cửa sổ lịch sử (A22) và ngày áp luật (A34). Chưa có cách đặt ngày
khác. Hệ quả cho bộ đánh giá:

1. Case 1 chạy hôm nay với file Tech manager đầy đủ thì lịch sử chứa cả đơn lên sau 21/09 (Sprint 10, các đơn cuối
   tháng 9): tool "nhìn thấy tương lai" và điểm cao giả.
2. Case 4 có luật ghi ngày: chạy lại sau ngày đó thì luật lặng lẽ hết hiệu lực, điểm trước và sau cải thiện không so
   được với nhau.

- [ ] **Thêm cờ `--today YYYY-MM-DD`: chạy như thể hôm nay là ngày đó, cho cả cửa sổ lịch sử và ngày áp luật (đề
      xuất).** Thay đổi nhỏ (spec §2, `cli.py`, test); các module `rules/` vẫn không đọc đồng hồ. Tên file output vẫn
      theo giờ thật. Đây là thay đổi hành vi nên cần bạn chốt.
- [ ] Không thêm cờ: script sinh dữ liệu cắt sẵn file lịch sử theo ngày cho case 1, 2; case 4 dùng luật không ghi
      ngày hoặc ngày ở xa; chấp nhận kết quả đổi khi qua ngày.

Trả lời:

### C2. Việc dở trong 2 case dựng lại

Trạng thái trong file là trạng thái ngày 06/10, không phải lúc sprint bắt đầu. Ví dụ dùng Sprint 8 làm sprint trước
của case 1: Sprint 8 đã xong 11/11 đơn nhưng còn 11 dòng `all issue` và 8 dòng `đã ro`, nên tool tính việc dở
LinhNV 5, AnTD 4, MinhNM 2, TiếnBV 0.

- [ ] **Bỏ sheet sprint trước: việc dở bằng 0, như backtest (A29) (đề xuất).** Không dùng trạng thái không đúng thời
      điểm. Tool sẽ báo `PREV-SPRINT-MISSING`, chấm cảnh báo bỏ qua dòng này. Việc dở được kiểm ở case 3.
- [ ] Giữ Sprint 8 nguyên trạng. Đo luôn ảnh hưởng của các dòng cũ chưa đóng trạng thái.

Trả lời:

### C3. Quy đổi giờ thật sang hạng để chấm độ lớn AI

Đề xuất: **≤ 8h = S, ≤ 24h = M, ≤ 48h = L, > 48h = XL** (giữa các mốc 4/16/32/64h của A7). Sprint 9: 2h, 4h → S;
10h, 17h, 17h, 22h → M; 26h, 26.5h → L; 57h, 58h, 68h, 83h → XL. Báo hai số: cùng hạng, và lệch đúng 1 hạng.

Lưu ý: giờ thật là tổng subtask sau khi làm xong, có thể gồm cả việc phát sinh; đây là thước đo gần đúng.

- [ ] Đồng ý
- [ ] Không đồng ý (ghi ranh giới khác):

Trả lời:

### C4. Gọi AI thế nào khi chạy đánh giá?

- [ ] **Mỗi case chạy `--ai gemini` 3 lần (đo dao động, D27) và 1 lần `--ai off` (chấm PIC không phụ thuộc AI)
      (đề xuất).** Tổng 15 lần gọi Gemini, mỗi lần 10–180 giây. `gemini` lỗi thì chuyển sang `agy` và ghi rõ trong
      báo cáo.
- [ ] Chỉ 1 lần `--ai gemini` mỗi case.
- [ ] Dùng `agy` thay `gemini`.

Trả lời:

---

## D. Lưu trữ và chấm điểm

### D1. Bộ dữ liệu đặt ở đâu?

- [ ] **Thư mục mới `eval/` ở gốc repo, commit cùng `input/` và `output/` (D18) (đề xuất):**

      ```
      eval/
      ├── README.md                 # cách sinh dữ liệu, chạy, chấm
      ├── build_cases.py            # sinh 5 bộ input (B5d)
      ├── score.py                  # chấm điểm (D2)
      ├── case-1-sprint-9/          # file sprint .xlsx, devs.xlsx, [luat.md], dap-an.md
      ├── case-2-sprint-8/
      ├── case-3-giua-sprint/
      ├── case-4-luat-tm/
      ├── case-5-du-lieu-ban/
      └── results/<YYYYMMDD-HHMM>/  # output của tool + bang-diem.md cho mỗi đợt
      ```

      Cập nhật `LLM.md` §3, §4 và `README.md`. Không đặt trong `tests/`: case 1, 2 chứa dữ liệu thật, mà dữ liệu từ
      `input/` không được chép vào fixture của test.
- [ ] Đặt trong thư mục plan của đợt này (`plans/261008-...`), coi là tài liệu một lần.

Trả lời:

### D2. Chấm điểm bằng tay hay bằng script?

- [ ] **Script `eval/score.py` đọc output của tool và `dap-an.md`, xuất `bang-diem.md` (đề xuất):** PIC khớp TM, PIC
      đúng spec, độ lớn cùng hạng / lệch 1 hạng, cảnh báo đúng / thiếu / thừa, dao động giữa các lần chạy AI. Sau
      mỗi lần cải thiện chạy lại để so điểm trước và sau. Không đưa vào `pytest`: đáp án "theo TM" là để đo, không
      phải để test pass/fail.
- [ ] Lần này mình chấm bằng tay và viết báo cáo; khi nào cần lặp lại thì mới viết script.

Trả lời:

---

## E. Sau khi chấm

### E1. Cải thiện tool tới mức nào?

- [ ] **Output sai so với spec (lỗi code): sửa luôn, kèm test. Đổi luật hoặc hành vi (thứ tự tiêu chí §7, giới hạn
      cân tải, prompt AI, ranh giới hạng): viết báo cáo đánh giá kèm file câu hỏi như file này, bạn chốt rồi mới sửa
      (đề xuất).** Đúng quy tắc của repo: thay đổi hành vi phải qua spec và `confirm.md` trước.
- [ ] Sửa luôn cả luật nếu điểm tăng, báo lại sau.
- [ ] Chỉ báo cáo, chưa sửa gì.

Trả lời:

### E2. Commit phần luật TM trước khi bắt đầu?

Phần luật TM (D28–D35) đang nằm trong working tree, chưa commit.

- [ ] **Chạy lint + test; xanh thì commit theo nhóm như các lần trước (`feat`, `test`, `docs`), rồi mới làm bộ dữ
      liệu (đề xuất).** Điểm "trước cải thiện" gắn với một commit, mỗi cải thiện sau có diff riêng.
- [ ] Chưa commit, để bạn tự commit.

Trả lời:

---

## Phần việc sau khi chốt (để bạn ước lượng, không cần trả lời)

| Bước | Việc |
|---|---|
| 0 | Commit phần luật TM (E2); thêm `--today` nếu C1 = có (spec §2, `cli.py`, test). |
| 1 | `eval/build_cases.py` sinh 5 case; `dap-an.md` phần "theo spec" mình tính tay; mẫu `dap-an.md` trống phần "theo TM" gửi TM điền (A3). |
| 2 | Chạy tool trên 5 case theo C4, lưu vào `eval/results/<ngày>/`. |
| 3 | `eval/score.py` chấm, viết báo cáo đánh giá: lỗi code tìm được, chỗ tool lệch TM và vì sao, độ lớn AI lệch thế nào. |
| 4 | Sửa lỗi code; với đề xuất đổi luật thì gửi file câu hỏi (E1); chạy lại để so điểm. |
