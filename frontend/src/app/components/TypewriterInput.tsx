import React, { useState, useEffect } from 'react';

const PLACEHOLDER_TEXTS = [
  "Enter website URL (e.g., https://example.com)",
  "Try https://www.orchids.app/",
  "Try https://www.youtube.com/",
  "Try https://spotify.com/"
];

const TYPING_SPEED = 50;
const DELETING_SPEED = 30;
const PAUSE_TIME = 2000;

interface TypewriterInputProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  className?: string;
}

export default function TypewriterInput({ value, onChange, className = '' }: TypewriterInputProps) {
  const [placeholderText, setPlaceholderText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);
  const [currentText, setCurrentText] = useState('');

  useEffect(() => {
    let timeout: NodeJS.Timeout;

    if (isTyping) {
      if (currentText.length < PLACEHOLDER_TEXTS[currentIndex].length) {
        timeout = setTimeout(() => {
          setCurrentText(PLACEHOLDER_TEXTS[currentIndex].slice(0, currentText.length + 1));
        }, TYPING_SPEED);
      } else {
        timeout = setTimeout(() => {
          setIsTyping(false);
        }, PAUSE_TIME);
      }
    } else {
      if (currentText.length > 0) {
        timeout = setTimeout(() => {
          setCurrentText(currentText.slice(0, -1));
        }, DELETING_SPEED);
      } else {
        setCurrentIndex((current) => (current + 1) % PLACEHOLDER_TEXTS.length);
        setIsTyping(true);
      }
    }

    return () => clearTimeout(timeout);
  }, [currentText, isTyping, currentIndex]);

  useEffect(() => {
    setPlaceholderText(currentText);
  }, [currentText]);

  return (
    <input
      type="url"
      value={value}
      onChange={onChange}
      placeholder={placeholderText}
      className={className}
      required
    />
  );
} 