import { WordGameLetter } from "./WordGameLetter";
import "./WordGameFoundWord.scss";

export const WordGameFoundWord = ({
  username,
  value,
  isRevealed,
}: {
  username: string;
  value: string;
  isRevealed: boolean;
}) => {
  return (
    <div className="word_game_found_word">
      <div className="word_game_found_word--username">{username}</div>
      <div className="word_game_found_word--value">
        {value.split("").map((letter, index) => (
          <WordGameLetter
            key={index}
            letter={letter}
            mini
            isRevealed={isRevealed}
          />
        ))}
      </div>
    </div>
  );
};
