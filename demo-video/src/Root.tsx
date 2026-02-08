import React from "react";
import { Composition } from "remotion";
import { AIBomDemo } from "./AIBomDemo";

export const Root: React.FC = () => {
  return (
    <Composition
      id="AIBomDemo"
      component={AIBomDemo}
      durationInFrames={540}
      fps={30}
      width={800}
      height={500}
    />
  );
};
