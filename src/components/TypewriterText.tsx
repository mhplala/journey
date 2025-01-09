import { useEffect, useState } from 'react';
import ReactMarkdown from 'react-markdown';

interface TypewriterTextProps {
  text: string;
}

function TypewriterText({ text }: TypewriterTextProps) {
  const [displayText, setDisplayText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (currentIndex < text.length) {
      const timer = setTimeout(() => {
        setDisplayText(text.slice(0, currentIndex + 1));
        setCurrentIndex(currentIndex + 1);
      }, 30);
      return () => clearTimeout(timer);
    }
  }, [currentIndex, text]);

  useEffect(() => {
    setDisplayText('');
    setCurrentIndex(0);
  }, [text]);

  return (
    <div className="min-h-[24px] prose prose-sm max-w-none dark:prose-invert">
      <ReactMarkdown>{displayText}</ReactMarkdown>
    </div>
  );
}

export default TypewriterText;
