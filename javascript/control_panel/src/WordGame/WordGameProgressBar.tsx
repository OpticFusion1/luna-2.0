import "./WordGameProgressBar.scss";

export const WordGameProgressBar = ({ animKey }: { animKey: number }) => {
  return (
    <div className="word_game_progress_bar">
      <div className={`fill animation--${animKey % 2 ? "shrink" : "expand"}`} />
    </div>
  );
};
