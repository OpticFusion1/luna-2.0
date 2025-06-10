import './Stopwatch.scss';
import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Helmet } from 'react-helmet';

const MAX_STOPWATCH_MS = 1000 * 60 * 60 * 24; // 24 hours

export const Stopwatch = () => {
  const animationRef = useRef<number | null>(null);
  const timestampStartRef = useRef(0);
  const elapsedBeforePauseRef = useRef(0); // Total ms accumulated so far
  const [isStarted, setIsStarted] = useState(false);

  const location = useLocation();

  const renderTime = (totalMs: number) => {
    const totalS = totalMs / 1000;
    const totalM = totalS / 60;
    const totalH = totalM / 60;
    const displayMs = ~~((totalMs % 1000) / 10);
    const displayS = ~~(totalS) % 60;
    const displayM = ~~(totalM) % 60;
    const displayH = ~~(totalH);

    const elHms = document.getElementById('stopwatch_text--hms');
    const elMs = document.getElementById('stopwatch_text--ms');
    if (elHms) {
      elHms.textContent = `${displayH < 10 ? '0' : ''}${displayH}:${displayM < 10 ? '0' : ''}${displayM}:${displayS < 10 ? '0' : ''}${displayS}`;
    }
    if (elMs) {
      elMs.textContent = `.${displayMs < 10 ? '0' : ''}${displayMs}`;
    }
  };

  const timerAnimation = (timestamp: number) => {
    const elapsed = timestamp - timestampStartRef.current + elapsedBeforePauseRef.current;
    const totalMs = elapsed;
    renderTime(totalMs);
    if (totalMs < MAX_STOPWATCH_MS) {
      animationRef.current = requestAnimationFrame(timerAnimation);
    }
  };
    
  const startOrPauseTimer = () => {
    if (!isStarted) {
      // RESUME: Start from where we left off
      timestampStartRef.current = performance.now();
      animationRef.current = requestAnimationFrame(timerAnimation);
    } else {
      // PAUSE: Record elapsed time so far
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      const now = performance.now();
      elapsedBeforePauseRef.current += now - timestampStartRef.current;
    }
    setIsStarted(!isStarted);
  };

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const h = parseInt(params.get('h') || '0', 10);
    const m = parseInt(params.get('m') || '0', 10);
    const s = parseInt(params.get('s') || '0', 10);
    const ms = parseInt(params.get('ms') || '0', 10);

    const initialOffsetMs = (((h * 60 + m) * 60 + s) * 1000 + ms * 10);
    elapsedBeforePauseRef.current = initialOffsetMs;
    renderTime(initialOffsetMs); // ⬅ display once on load

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [location.search]);

  return (
    <div className='stopwatch'>
      <Helmet><title>Heavenfire Stopwatch</title></Helmet>

      <div className='stopwatch_container'>
        <div className='stopwatch_text_container'>
          <span className='stopwatch_text' id='stopwatch_text--hms'>00:00:00</span>
          <span className='stopwatch_text' id='stopwatch_text--ms'>.00</span>
        </div>
        <br />
        <button onClick={startOrPauseTimer}>{isStarted ? 'pause' : 'start'}</button>
      </div>
    </div>
  );
};
