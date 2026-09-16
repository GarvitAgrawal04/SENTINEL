import { useState, useEffect, useRef } from 'react';

const CHARS = '#$%^&@X*0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';

export default function useScrambleText(text, play = true, duration = 1500) {
  const [displayText, setDisplayText] = useState(text);
  const frameRef = useRef();

  useEffect(() => {
    if (!play) {
      setDisplayText(text);
      return;
    }
    
    let start = null;
    const animate = (timestamp) => {
      if (!start) start = timestamp;
      const progress = Math.min((timestamp - start) / duration, 1);
      
      if (progress < 1) {
        let scrambled = '';
        for (let i = 0; i < text.length; i++) {
          // As progress goes from 0 to 1, more characters settle to their final state
          if (text[i] === ' ' || Math.random() < progress) {
            scrambled += text[i];
          } else {
            scrambled += CHARS[Math.floor(Math.random() * CHARS.length)];
          }
        }
        setDisplayText(scrambled);
        frameRef.current = requestAnimationFrame(animate);
      } else {
        setDisplayText(text);
      }
    };
    
    frameRef.current = requestAnimationFrame(animate);
    
    return () => cancelAnimationFrame(frameRef.current);
  }, [text, play, duration]);

  return displayText;
}
