import { useEffect, useRef, useState } from "react";
import { wordlist } from "./wordlist";
import { WordGameLetter } from "./WordGameLetter";
import { FoundWord } from "../types";
import { WordGameFoundWord } from "./WordGameFoundWord";
import { WordGameProgressBar } from "./WordGameProgressBar";
import "./WordGame.scss";

const lunaScramble = (str: string) => {
  var arr = str.split("");
  for (var i = arr.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var temp = arr[i];
    arr[i] = arr[j];
    arr[j] = temp;
  }
  return arr.join("");
};

export const WordGame = () => {
  const wsRef = useRef<WebSocket | null>(null);
  const gameTimeoutRef = useRef<number | NodeJS.Timer>();
  const gameResetTimeoutRef = useRef<number | NodeJS.Timer>();

  const gameWordsRef = useRef<Set<string>>(new Set());
  const [gameLetters, setGameLetters] = useState("");
  const [foundWords, setFoundWords] = useState<(FoundWord | number)[]>([]);

  const [progressBarAnimKey, setProgressBarAnimKey] = useState(0);

  const revealWords = () => {
    setFoundWords((prevState) => {
      const newState = [...prevState];
      for (let i = 0; i < newState.length; i++) {
        if (typeof newState[i] === "number") {
          for (const word of gameWordsRef.current) {
            if (word.length === newState[i]) {
              newState[i] = {
                value: word,
                username: "",
                isRevealed: true,
              };
              gameWordsRef.current.delete(word);
            }
          }
        }
      }
      return newState;
    });
  };

  const resetGame = () => {
    const words = Object.keys(wordlist);
    const sevenLetterWords = words.filter((word) => word.length === 7);
    const mainWord =
      sevenLetterWords[~~(Math.random() * sevenLetterWords.length)];
    const mainWordFrequencyMap = wordlist[mainWord];
    const possibleWords = [];
    for (let i = 0; i < words.length; i++) {
      const candidateFrequencyMap = wordlist[words[i]];
      const candidateFrequencyMapKeys = Object.keys(candidateFrequencyMap);
      for (let j = 0; j < candidateFrequencyMapKeys.length; j++) {
        const letter = candidateFrequencyMapKeys[j];
        if (
          !mainWordFrequencyMap.hasOwnProperty(letter) ||
          mainWordFrequencyMap[letter] < candidateFrequencyMap[letter]
        ) {
          break;
        }
        if (j === candidateFrequencyMapKeys.length - 1) {
          possibleWords.push(words[i]);
        }
      }
    }
    possibleWords.sort((a, b) => b.length - a.length);
    gameWordsRef.current = new Set(possibleWords);
    // console.log(possibleWords);
    setGameLetters(lunaScramble(possibleWords[0]));
    const _foundWords = [];
    const freqMap: { [key: string]: number } = {};
    // 2346
    const wordLengthCounts: { [key: string]: number } = {
      7: 2,
      6: 3,
      5: 4,
      4: 5,
    };
    for (let i = 0; i < possibleWords.length; i++) {
      const word = possibleWords[i];
      freqMap[word.length] = freqMap[word.length]
        ? freqMap[word.length] + 1
        : 1;
      if (freqMap[word.length] <= wordLengthCounts[word.length]) {
        _foundWords.push(word.length);
      }
    }
    setFoundWords(_foundWords);
    setProgressBarAnimKey((prevState) => prevState + 1);
    gameTimeoutRef.current = setTimeout(() => {
      revealWords();
      setProgressBarAnimKey((prevState) => prevState + 1);
    }, 120000); // 2 minutes
    gameResetTimeoutRef.current = setTimeout(() => {
      resetGame();
    }, 120000 + 30000); // 2 minutes + 30 seconds
  };

  useEffect(() => {
    resetGame();

    return () => {
      clearTimeout(gameTimeoutRef.current);
      clearTimeout(gameResetTimeoutRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    const ws = new WebSocket("ws://localhost:4000");
    wsRef.current = ws;
    ws.addEventListener("open", () => {
      console.log("Connected to WebSocket server!");
    });
    ws.addEventListener("message", (_data) => {
      const data = JSON.parse(_data.data);
      if (data.hasOwnProperty("twitch_event")) {
        if (data.twitch_event.event === "MESSAGE") {
          if (data.twitch_event.value.trim().split(" ").length === 1) {
            const username = data.twitch_event.username;
            const value = data.twitch_event.value.trim().toLowerCase();
            // console.log(`${username} guessed ${value}`);
            if (gameWordsRef.current.has(value)) {
              gameWordsRef.current.delete(value);
              setFoundWords((prevState) => {
                const newState = [...prevState];
                for (let i = 0; i < newState.length; i++) {
                  if (newState[i] === value.length) {
                    newState[i] = { username, value, isRevealed: false };
                    return newState;
                  }
                }
                return prevState;
              });
            }
          }
        }
      }
    });

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="word_game">
      <div className="word_game_container">
        <div className="title">
          <div>Luna's Word Game</div>
          <img
            className="luna_portrait"
            alt="luna"
            src="luna_portrait.png"
            width="88px"
            height="88px"
          />
        </div>
        <div className="game_letters">
          {gameLetters.split("").map((letter, index) => (
            <WordGameLetter key={index} letter={letter} />
          ))}
        </div>
        <WordGameProgressBar
          key={progressBarAnimKey}
          animKey={progressBarAnimKey}
        />
        <div className="found_words">
          {foundWords.map((i, index) =>
            typeof i === "number" ? (
              <div key={index} className="ghost_word">
                {Array(i)
                  .fill(null)
                  .map((item, index) => (
                    <div key={index} className="ghost_letter" />
                  ))}
              </div>
            ) : (
              <WordGameFoundWord
                key={index}
                username={i.username}
                value={i.value}
                isRevealed={i.isRevealed}
              />
            )
          )}
        </div>
      </div>
    </div>
  );
};
