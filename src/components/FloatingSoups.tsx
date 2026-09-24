import * as THREE from 'three'
import { Suspense, useEffect, useMemo, useRef } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { ContactShadows } from '@react-three/drei/core/ContactShadows'
import { OrbitControls } from '@react-three/drei/core/OrbitControls'
import { useGLTF } from '@react-three/drei/core/Gltf'
import { Html } from '@react-three/drei/web/Html'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'

const MODEL_URL = `${import.meta.env.BASE_URL}models/realistic-soup.glb`
const TARGET = new THREE.Vector3(0, 0.36, 0)
const INSPECT_POSITION = new THREE.Vector3(2.5, 3.1, 4.3)
const FIELD_POSITION = new THREE.Vector3(0, 0, 10)

interface SceneProps {
  closeUp: boolean
  paused: boolean
  reducedMotion: boolean
}

function useSoupParts() {
  const { scene } = useGLTF(MODEL_URL, false)
  return useMemo(() => {
    const parts: THREE.Mesh[] = []
    scene.updateMatrixWorld(true)
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) parts.push(object)
    })
    return parts
  }, [scene])
}

function StudioLighting({ shadows }: { shadows: boolean }) {
  const { gl, scene } = useThree()
  useEffect(() => {
    // Local studio reflections: the model never depends on a third-party HDR URL.
    const room = new RoomEnvironment()
    const generator = new THREE.PMREMGenerator(gl)
    const environment = generator.fromScene(room, 0.04)
    scene.environment = environment.texture
    scene.environmentIntensity = 0.5
    room.dispose()
    generator.dispose()
    return () => {
      scene.environment = null
      environment.dispose()
    }
  }, [gl, scene])
  return (
    <>
      <ambientLight intensity={0.15} />
      <directionalLight position={[-3, 6, 4]} intensity={2.5} color='#fff1df' castShadow={shadows} shadow-mapSize={[2048, 2048]} shadow-camera-left={-2} shadow-camera-right={2} shadow-camera-top={2} shadow-camera-bottom={-2} shadow-normalBias={0.008} shadow-bias={-0.0001} />
      <directionalLight position={[4, 3, -4]} intensity={0.8} color='#ffffff' />
    </>
  )
}

function Steam({ paused }: { paused: boolean }) {
  const group = useRef<THREE.Group>(null)
  const elapsed = useRef(0)
  const texture = useMemo(() => {
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = 64
    const ctx = canvas.getContext('2d')!
    const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
    gradient.addColorStop(0, 'rgba(255,255,255,0.35)')
    gradient.addColorStop(0.35, 'rgba(255,255,255,0.15)')
    gradient.addColorStop(1, 'rgba(255,255,255,0)')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, 64, 64)
    return new THREE.CanvasTexture(canvas)
  }, [])
  useEffect(() => () => texture.dispose(), [texture])
  useFrame((_, dt) => {
    if (!group.current || paused) return
    elapsed.current += Math.min(dt, 0.05)
    group.current.children.forEach((child, i) => {
      const age = (elapsed.current * 0.22 + i / 14) % 1
      const sprite = child as THREE.Sprite
      sprite.position.set(
        Math.sin(i * 2.4) * 0.45 + Math.sin(age * 5 + i) * age * 0.13,
        0.69 + age * 1.25,
        Math.cos(i * 2.4) * 0.35,
      )
      sprite.scale.set(0.16 + age * 0.3, 0.3 + age * 0.7, 1)
      ;(sprite.material as THREE.SpriteMaterial).opacity = Math.sin(age * Math.PI) * 0.28
    })
  })
  return (
    <group ref={group}>
      {Array.from({ length: 14 }, (_, i) => (
        <sprite key={i} position={[0, 0.7, 0]}>
          <spriteMaterial map={texture} transparent opacity={0} depthWrite={false} />
        </sprite>
      ))}
    </group>
  )
}

function CloseUpSoup({ paused }: { paused: boolean }) {
  const parts = useSoupParts()
  return (
    <group>
      {parts.map((part) => (
        <mesh castShadow receiveShadow key={part.uuid} geometry={part.geometry} material={part.material} matrix={part.matrixWorld} matrixAutoUpdate={false} dispose={null} />
      ))}
      <Steam paused={paused} />
      <ContactShadows position={[0, -0.015, 0]} opacity={0.38} scale={7} blur={2.8} far={2} resolution={512} frames={1} color='#55331d' />
    </group>
  )
}

function SoupField({ paused }: { paused: boolean }) {
  const parts = useSoupParts()
  const { viewport, camera, size } = useThree()
  const count = size.width < 600 ? 16 : 36
  const instances = useRef<(THREE.InstancedMesh | null)[]>([])
  const dummy = useMemo(() => new THREE.Object3D(), [])
  const matrix = useMemo(() => new THREE.Matrix4(), [])
  const time = useRef(0)
  const bowls = useMemo(() => Array.from({ length: count }, (_, i) => {
    const z = 4 + (i / count) * 40
    const { width, height } = viewport.getCurrentViewport(camera, [0, 0, -z])
    // A stable distribution keeps resizing and pause/resume from respawning bowls.
    const random = (seed: number) => THREE.MathUtils.euclideanModulo(Math.sin(seed * 127.1) * 43758.5453, 1)
    return {
      x: (random(i + 1) - 0.5) * width,
      y: (random(i + 52) - 0.5) * height,
      z, width, height,
      angle: random(i + 100) * Math.PI * 2,
      spin: random(i + 200) * Math.PI * 2,
    }
  }), [count, viewport, camera])

  useFrame((_, dt) => {
    if (!paused) time.current += Math.min(dt, 0.05)
    bowls.forEach((bowl, i) => {
      const t = time.current
      const x = THREE.MathUtils.euclideanModulo(bowl.x + Math.cos(bowl.angle) * t * 0.45 + bowl.width * 0.65, bowl.width * 1.3) - bowl.width * 0.65
      const y = THREE.MathUtils.euclideanModulo(bowl.y + Math.sin(bowl.angle) * t * 0.45 + bowl.height * 0.65, bowl.height * 1.3) - bowl.height * 0.65
      dummy.position.set(x, y, -bowl.z)
      dummy.rotation.set(0.55 + Math.sin(t * 0.14 + bowl.spin) * 0.65, bowl.spin + t * 0.12, Math.cos(bowl.spin + t * 0.1) * 0.35)
      dummy.updateMatrix()
      parts.forEach((part, partIndex) => {
        matrix.multiplyMatrices(dummy.matrix, part.matrixWorld)
        instances.current[partIndex]?.setMatrixAt(i, matrix)
      })
    })
    instances.current.forEach((instance) => {
      if (instance) instance.instanceMatrix.needsUpdate = true
    })
  })
  return (
    <group>
      {parts.map((part, i) => (
        <instancedMesh
          key={`${part.uuid}-${count}`}
          ref={(instance) => { instances.current[i] = instance }}
          args={[part.geometry, part.material, count]}
          frustumCulled={false}
          dispose={null}
        />
      ))}
    </group>
  )
}

function Scene({ closeUp, paused, reducedMotion }: SceneProps) {
  const { camera, size, invalidate } = useThree()
  useEffect(() => {
    const perspective = camera as THREE.PerspectiveCamera
    perspective.position.copy(closeUp ? INSPECT_POSITION : FIELD_POSITION)
    // Keep the complete bowl in frame on portrait phones.
    perspective.fov = closeUp ? (size.width < 600 ? 56 : 34) : 24
    perspective.lookAt(closeUp ? TARGET : new THREE.Vector3())
    perspective.updateProjectionMatrix()
    invalidate()
  }, [camera, closeUp, size.width, invalidate])
  return (
    <>
      <color attach='background' args={[closeUp ? '#f2e5cf' : '#ffbf40']} />
      <StudioLighting shadows={closeUp} />
      <Suspense fallback={<Html center><div className='loading' role='status'>Simmering…</div></Html>}>
        {closeUp ? <CloseUpSoup paused={paused || reducedMotion} /> : <SoupField paused={paused || reducedMotion} />}
      </Suspense>
      {closeUp && <OrbitControls key='inspect' target={TARGET} enablePan={false} minDistance={3.3} maxDistance={8} minPolarAngle={0.18} maxPolarAngle={Math.PI / 2 - 0.03} autoRotate={!paused && !reducedMotion} autoRotateSpeed={0.35} />}
    </>
  )
}

export default function FloatingSoups(props: SceneProps) {
  return (
    <Canvas
      shadows
      frameloop={props.paused || props.reducedMotion ? 'demand' : 'always'}
      gl={{ antialias: true, toneMapping: THREE.ACESFilmicToneMapping, toneMappingExposure: 1.05 }}
      dpr={[1, 1.5]}
      camera={{ position: [0, 0, 10], fov: 24, near: 0.1, far: 100 }}
      aria-label={props.closeUp ? 'Interactive realistic noodle soup. Drag to orbit and scroll to zoom.' : 'Floating bowls of realistic noodle soup.'}
      fallback={<p className='loading'>Your browser needs WebGL to serve this soup.</p>}
    >
      <Scene {...props} />
    </Canvas>
  )
}
