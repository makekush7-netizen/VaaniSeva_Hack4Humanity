import React, { Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { Environment, OrbitControls, useGLTF } from '@react-three/drei'

function VaaniModel() {
  const { scene } = useGLTF('/models/vaani.glb')
  return <primitive object={scene} />
}

export default function AvatarShowcase() {
  return (
    <div className="relative h-72 overflow-hidden rounded-3xl bg-gradient-to-b from-amber-50 to-orange-100">
      <Canvas camera={{ position: [0, 1.55, 1.2], fov: 28 }} dpr={[1, 1.5]} onCreated={({ camera }) => camera.lookAt(0, 1.52, 0)}>
        <ambientLight intensity={1.8} />
        <directionalLight position={[2, 4, 3]} intensity={2.5} />
        <Suspense fallback={null}>
          <VaaniModel />
          <Environment preset="studio" />
        </Suspense>
        <OrbitControls target={[0, 1.52, 0]} enablePan={false} enableZoom={false} minPolarAngle={1.25} maxPolarAngle={1.75} />
      </Canvas>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/80 to-transparent px-5 pb-4 pt-12 text-white">
        <p className="font-semibold">Arya · multilingual guide</p>
        <p className="text-xs text-white/75">A familiar face for assisted digital access</p>
      </div>
    </div>
  )
}

useGLTF.preload('/models/vaani.glb')
