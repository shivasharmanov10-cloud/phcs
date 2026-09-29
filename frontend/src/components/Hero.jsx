
import { useEffect, useState } from "react";

import {
  ArrowRight,
  BrainCircuit,
  HeartPulse,
} from "lucide-react";

function Hero({
  onExplore,
  onRisk,
}) {
  const words = [
    "smarter medicine.",
    "safer healthcare.",
    "stronger communities.",
  ];

  const [wordIndex, setWordIndex] = useState(0);
  const [text, setText] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    const currentWord = words[wordIndex];

    const speed = deleting ? 45 : 85;

    const timer = setTimeout(() => {
      if (!deleting) {
        const nextText =
          currentWord.substring(
            0,
            text.length + 1
          );

        setText(nextText);

        if (nextText === currentWord) {
          setTimeout(() => {
            setDeleting(true);
          }, 1300);
        }
      } else {
        const nextText =
          currentWord.substring(
            0,
            text.length - 1
          );

        setText(nextText);

        if (nextText === "") {
          setDeleting(false);

          setWordIndex(
            (previous) =>
              (previous + 1) % words.length
          );
        }
      }
    }, speed);

    return () => clearTimeout(timer);
  }, [text, deleting, wordIndex]);

  return (
    <section className="hero-card">

      <div className="hero-content">

        <div className="hero-badge">
          <BrainCircuit size={16} />
          AI-POWERED PUBLIC HEALTH
        </div>

        <h1>
          Predict demand.
          <br />

          <span className="hero-gradient">
            {text}
            <span className="typing-cursor">
              |
            </span>
          </span>
        </h1>

        <p>
          Predict medicine demand, detect
          stock risks, identify anomalies,
          and recommend redistribution before
          shortages affect communities.
        </p>

        <div className="hero-actions">

          <button
            className="primary-button"
            onClick={onExplore}
          >
            Explore predictions
            <ArrowRight size={18} />
          </button>

          <button
            className="secondary-button"
            onClick={onRisk}
          >
            View risk analysis
          </button>

        </div>

      </div>

      <div className="hero-visual">

        <div className="hero-orbit orbit-one"></div>
        <div className="hero-orbit orbit-two"></div>

        <div className="hero-heart">
          <HeartPulse size={76} />
        </div>

        <div className="floating-card floating-one">
          <strong>ML Active</strong>
          <span>Prediction engine</span>
        </div>

        <div className="floating-card floating-two">
          <strong>48</strong>
          <span>Medicine records</span>
        </div>

      </div>

    </section>
  );
}

export default Hero;