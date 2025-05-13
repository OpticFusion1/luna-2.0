import "./WordGameLetter.scss";

export const WordGameLetter = ({
  letter = "",
  mini = false,
  isRevealed = false,
}: {
  letter: string;
  mini?: boolean;
  isRevealed?: boolean;
}) => {
  return (
    <div
      className={`word_game_letter ${mini ? "mini" : ""} ${
        isRevealed ? "is_revealed" : ""
      }`}
    >
      {letter.toUpperCase()}
    </div>
  );
};
