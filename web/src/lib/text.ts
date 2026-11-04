// Text helpers shared by search boxes.

/** Lower-case and fold Turkish letters so "meşe", "mese" and "MEŞE" all match. */
export function normalize(text: string): string {
  return text
    .replace(/İ/g, "i")
    .replace(/I/g, "i")
    .toLowerCase()
    .replace(/ı/g, "i")
    .replace(/ş/g, "s")
    .replace(/ğ/g, "g")
    .replace(/ü/g, "u")
    .replace(/ö/g, "o")
    .replace(/ç/g, "c")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

/** "Quercus robur" -> "quercus-robur" */
export function slugify(name: string): string {
  return name.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z-]/g, "");
}
