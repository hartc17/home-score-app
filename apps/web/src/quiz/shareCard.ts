const CARD_WIDTH = 1200;
const CARD_HEIGHT = 630;

function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

function blendLine(blend: Record<string, number>): string {
  return Object.entries(blend)
    .sort((a, b) => b[1] - a[1])
    .map(([style, share]) => `${style} ${Math.round(share * 100)}%`)
    .join("   ·   ");
}

export function buildShareCardSvg(name: string, blend: Record<string, number>): string {
  const title = "MY HOUSE FLAVOR";
  const line = escapeXml(blendLine(blend));
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${CARD_WIDTH}" height="${CARD_HEIGHT}" viewBox="0 0 ${CARD_WIDTH} ${CARD_HEIGHT}">
  <rect width="${CARD_WIDTH}" height="${CARD_HEIGHT}" fill="#292524"/>
  <text x="${CARD_WIDTH / 2}" y="188" text-anchor="middle" font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif" font-size="30" letter-spacing="8" fill="#a8a29e">${title}</text>
  <text x="${CARD_WIDTH / 2}" y="330" text-anchor="middle" font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif" font-size="94" font-weight="700" fill="#fafaf9">${escapeXml(name)}</text>
  <text x="${CARD_WIDTH / 2}" y="416" text-anchor="middle" font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif" font-size="34" fill="#d6d3d1" style="text-transform:capitalize">${line}</text>
  <text x="${CARD_WIDTH / 2}" y="560" text-anchor="middle" font-family="system-ui, -apple-system, Segoe UI, Roboto, sans-serif" font-size="26" letter-spacing="2" fill="#78716c">HouseFlavor</text>
</svg>`;
}

async function svgToPngBlob(svg: string): Promise<Blob> {
  const url = URL.createObjectURL(new Blob([svg], { type: "image/svg+xml" }));
  try {
    const image = new Image();
    image.width = CARD_WIDTH;
    image.height = CARD_HEIGHT;
    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("share card render failed"));
      image.src = url;
    });
    const canvas = document.createElement("canvas");
    canvas.width = CARD_WIDTH;
    canvas.height = CARD_HEIGHT;
    canvas.getContext("2d")!.drawImage(image, 0, 0);
    return await new Promise<Blob>((resolve, reject) =>
      canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error("share card encode failed"))), "image/png"),
    );
  } finally {
    URL.revokeObjectURL(url);
  }
}

// Web Share with a file when the browser supports it, otherwise a download.
export async function shareCard(name: string, blend: Record<string, number>): Promise<void> {
  const blob = await svgToPngBlob(buildShareCardSvg(name, blend));
  const filename = `house-flavor-${name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}.png`;
  const file = new File([blob], filename, { type: "image/png" });

  if (navigator.canShare?.({ files: [file] })) {
    await navigator.share({ files: [file], title: "My house flavor", text: `My house flavor is ${name}.` });
    return;
  }

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
