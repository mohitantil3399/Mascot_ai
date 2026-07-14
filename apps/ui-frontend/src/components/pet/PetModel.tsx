// apps/ui-frontend/src/components/pet/PetModel.tsx
import React, { useRef, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import { useGLTF, useAnimations, Center } from '@react-three/drei';
import * as THREE from 'three';
import soldierUrl from './Soldier.glb';

export default function PetModel({ animState }: { animState: 'idle' | 'thinking' | 'talking' }) {
  const groupRef = useRef<THREE.Group>(null);
  const ringRef = useRef<THREE.Mesh>(null);
  
  // Load the Soldier GLTF model and its animations
  const { scene, animations } = useGLTF(soldierUrl);
  const { actions } = useAnimations(animations, groupRef);

  useEffect(() => {
    // Traverse model to ensure proper lighting response on all materials
    scene.traverse((child: any) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;
      }
    });
  }, [scene]);

  useEffect(() => {
    // Soldier.glb typically contains ['Idle', 'Run', 'TPose', 'Walk']
    // We transition between actions smoothly based on animState
    let actionName = 'Idle';
    if (animState === 'thinking') {
      actionName = actions['Walk'] ? 'Walk' : 'Idle';
    } else if (animState === 'talking') {
      actionName = actions['Run'] ? 'Run' : (actions['Walk'] ? 'Walk' : 'Idle');
    } else {
      actionName = actions['Idle'] ? 'Idle' : (Object.keys(actions)[0] || '');
    }

    const currentAction = actions[actionName];
    if (currentAction) {
      currentAction.reset().fadeIn(0.3).play();
      return () => {
        currentAction.fadeOut(0.3);
      };
    }
  }, [animState, actions]);

  useFrame((state, delta) => {
    if (!groupRef.current) return;
    
    // Gentle floating and state-based rotations
    const time = state.clock.getElapsedTime();
    
    if (animState === 'thinking') {
      groupRef.current.rotation.y += delta * 1.5;
    } else if (animState === 'talking') {
      groupRef.current.rotation.y = Math.sin(time * 4) * 0.2;
    } else {
      groupRef.current.rotation.y = Math.sin(time * 0.8) * 0.15;
    }

    if (ringRef.current) {
      ringRef.current.rotation.z += delta * 1.5;
      ringRef.current.rotation.x = Math.sin(time) * 0.5;
    }
  });

  return (
    <group ref={groupRef} position={[0, 0, 0]} scale={[0.85, 0.85, 0.85]}>
      {/* Centered Soldier Character Model */}
      <Center position={[0, 0, 0]}>
        <primitive object={scene} />
      </Center>

      {/* Orbiting Pedestal Ring right under feet */}
      <mesh ref={ringRef} position={[0, -0.82, 0]}>
        <torusGeometry args={[1.0, 0.04, 16, 64]} />
        <meshStandardMaterial 
          color="#c084fc" 
          emissive="#a855f7" 
          emissiveIntensity={0.8}
          transparent
          opacity={0.85}
        />
      </mesh>
    </group>
  );
}

useGLTF.preload(soldierUrl);
