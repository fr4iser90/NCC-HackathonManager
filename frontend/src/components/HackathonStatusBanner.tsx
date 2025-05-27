import React from "react";
import clsx from "clsx";

type HackathonStatusBannerProps = {
  hackathonName: string;
  timeLeft: string;
  started: boolean;
};

export default function HackathonStatusBanner({
  hackathonName,
  timeLeft,
  started,
}: HackathonStatusBannerProps) {
  return (
    <div
      className={clsx(
        "px-4 py-1 rounded-md font-semibold text-sm flex items-center gap-2",
        started
          ? "bg-green-600 text-white animate-pulse"
          : "bg-blue-600 text-white"
      )}
      title={started ? "Hackathon läuft!" : "Hackathon startet bald"}
    >
      <span>
        {hackathonName}{" "}
        {started ? (
          <span className="font-bold animate-pulse">läuft!</span>
        ) : (
          <>
            startet in: <span className="font-mono">{timeLeft}</span>
          </>
        )}
      </span>
    </div>
  );
}
