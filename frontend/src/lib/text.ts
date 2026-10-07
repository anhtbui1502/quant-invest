/** Bỏ dấu tiếng Việt, viết thường: "Hòa Phát" -> "hoa phat". */
export function fold(text: string): string {
  return text
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase();
}
