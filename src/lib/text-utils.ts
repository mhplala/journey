export function formatMessageText(text: string): string {
  if (!text) return '';
  
  return text
    // Fix concatenated words by adding spaces between them
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    // Add space after punctuation if missing
    .replace(/([.,!?])([^\s])/g, '$1 $2')
    // Preserve markdown bold/italic
    .replace(/\*\*(.*?)\*\*/g, (match) => match)
    .replace(/\*(.*?)\*/g, (match) => match)
    // Preserve code blocks
    .replace(/`(.*?)`/g, (match) => match)
    // Fix emojis getting split
    .replace(/([\u{1F300}-\u{1F9FF}])/gu, ' $1 ')
    // Clean up multiple spaces
    .replace(/\s+/g, ' ')
    .trim();
}
