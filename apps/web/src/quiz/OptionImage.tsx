import type { QuizOption } from "./questions.ts";
import { Plate } from "./Plate.tsx";

// The single swap seam: a curated photo when the option carries one, otherwise
// the neutral SVG stand-in. The alt text stays neutral so the image never
// captions the choice, per the preference-neutrality requirement.
export function OptionImage({ option }: { option: QuizOption }) {
  if (option.photo) {
    return <img src={option.photo} alt="room option" className="h-full w-full object-cover" />;
  }
  return <Plate spec={option.plate} />;
}
