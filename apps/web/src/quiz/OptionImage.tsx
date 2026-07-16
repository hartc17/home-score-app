import type { QuizOption } from "./questions.ts";
import { Scene } from "./scene/Scene.tsx";

// The single swap seam: a curated photo when the option carries one, otherwise
// the parametric scene. The alt text stays neutral so the image never captions
// the choice, per the preference-neutrality requirement.
export function OptionImage({ option }: { option: QuizOption }) {
  if (option.photo) {
    return <img src={option.photo} alt="room option" className="h-full w-full object-cover" />;
  }
  return <Scene spec={option.scene} />;
}
