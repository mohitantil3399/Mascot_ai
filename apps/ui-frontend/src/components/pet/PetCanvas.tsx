// apps/ui-frontend/src/components/pet/PetCanvas.tsx
import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { Float } from '@react-three/drei';
import PetModel from './PetModel';

export default function PetCanvas({ animState }: { animState: 'idle' | 'thinking' | 'talking' }) {
  return (
    <Canvas
      gl={{ antialias: true, alpha: true }}
      camera={{ position: [0, 0.15, 3.6], fov: 45 }}
      style={{ background: 'transparent' }}
    >
      <ambientLight intensity={1.2} />
      <directionalLight position={[5, 10, 5]} intensity={1.8} />
      <directionalLight position={[-5, -5, -5]} intensity={0.8} />
      <Suspense fallback={null}>
        <Float speed={1.5} rotationIntensity={0.15} floatIntensity={0.18}>
          <PetModel animState={animState} />
        </Float>
      </Suspense>
    </Canvas>
  );
}
