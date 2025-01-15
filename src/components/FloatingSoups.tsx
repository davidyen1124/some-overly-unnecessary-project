import * as THREE from 'three'
import { useRef, useState, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { Environment } from '@react-three/drei'
import {
  EffectComposer,
  DepthOfField,
  ToneMapping
} from '@react-three/postprocessing'
import { nanoid } from 'nanoid'

function BowlAndSoup() {
  const bowlRef = useRef<THREE.Group>(null)

  const outerPoints = [
    new THREE.Vector2(0.0, 0.0),
    new THREE.Vector2(0.7, 0.0),
    new THREE.Vector2(0.9, 0.3),
    new THREE.Vector2(0.85, 0.6)
  ]

  const innerPoints = [
    new THREE.Vector2(0.0, 0.0),
    new THREE.Vector2(0.68, 0.0),
    new THREE.Vector2(0.88, 0.27),
    new THREE.Vector2(0.83, 0.57)
  ]

  useFrame(() => {
    if (!bowlRef.current) return
    bowlRef.current.rotation.y += 0.001
  })

  return (
    <group ref={bowlRef}>
      <mesh receiveShadow castShadow>
        <latheGeometry args={[outerPoints, 32]} />
        <meshPhysicalMaterial
          color='#f8f8f8'
          metalness={0.1}
          roughness={0.4}
          clearcoat={1}
          clearcoatRoughness={0.2}
        />
      </mesh>

      <mesh receiveShadow castShadow>
        <latheGeometry args={[innerPoints, 32]} />
        <meshPhysicalMaterial
          color='#ebe7e7'
          metalness={0.05}
          roughness={0.5}
          clearcoat={0.8}
          clearcoatRoughness={0.3}
          side={THREE.BackSide}
        />
      </mesh>

      <mesh position={[0, 0.58, 0]} receiveShadow castShadow>
        <cylinderGeometry args={[0.69, 0.69, 0.02, 32]} />
        <meshPhysicalMaterial color='#5c2b1c' metalness={0} roughness={0.7} />
      </mesh>
    </group>
  )
}

class SteamPuff {
  readonly id: string
  x: number
  y: number
  z: number
  age: number
  spheres: { x: number; y: number; z: number; baseScale: number }[]
  private static readonly LIFESPAN = 3.0
  private static readonly FADE_IN = 0.5
  private static readonly FADE_OUT = 0.7
  private centerX: number
  private centerZ: number
  private swirlAngle: number
  private swirlRadius: number
  private swirlSpeed: number
  private swirlSpeedDelta: number
  private driftX: number
  private driftZ: number

  constructor() {
    this.id = nanoid()
    this.x = (Math.random() - 0.5) * 0.6
    this.y = 0.4
    this.z = (Math.random() - 0.5) * 0.6
    this.age = 0
    this.centerX = this.x
    this.centerZ = this.z
    this.swirlAngle = Math.random() * Math.PI * 2
    this.swirlRadius = 0.05 + Math.random() * 0.05
    this.swirlSpeed = 0.5 + Math.random() * 0.5
    this.swirlSpeedDelta = (Math.random() - 0.5) * 0.1
    this.driftX = (Math.random() - 0.5) * 0.02
    this.driftZ = (Math.random() - 0.5) * 0.02

    this.spheres = Array.from({ length: 4 }, () => ({
      x: (Math.random() - 0.5) * 0.3,
      y: Math.random() * 0.2,
      z: (Math.random() - 0.5) * 0.3,
      baseScale: 0.3 + Math.random() * 0.2
    }))
  }

  update(delta: number) {
    this.age += delta
    this.swirlSpeed += this.swirlSpeedDelta * delta
    if (this.swirlSpeed < 0.2) this.swirlSpeed = 0.2
    if (this.swirlSpeed > 1.0) this.swirlSpeed = 1.0
    this.swirlAngle += this.swirlSpeed * delta
    this.x = this.centerX + this.swirlRadius * Math.cos(this.swirlAngle)
    this.z = this.centerZ + this.swirlRadius * Math.sin(this.swirlAngle)
    this.x += this.driftX * delta
    this.z += this.driftZ * delta
    this.y += delta * 0.4
  }

  isAlive(): boolean {
    return this.age <= SteamPuff.LIFESPAN
  }

  getOpacity(): number {
    if (this.age < SteamPuff.FADE_IN) {
      return this.age / SteamPuff.FADE_IN
    }
    if (this.age > SteamPuff.LIFESPAN - SteamPuff.FADE_OUT) {
      const fadeTime = this.age - (SteamPuff.LIFESPAN - SteamPuff.FADE_OUT)
      return 1 - fadeTime / SteamPuff.FADE_OUT
    }
    return 1
  }

  getSphereScale(baseScale: number): number {
    const minScale = 0.1 * baseScale
    if (this.age < SteamPuff.FADE_IN) {
      const t = this.age / SteamPuff.FADE_IN
      return minScale + t * (baseScale - minScale)
    }
    return baseScale
  }
}

function NaturalSteam() {
  const [puffs, setPuffs] = useState<SteamPuff[]>([])

  useEffect(() => {
    let timeoutId: ReturnType<typeof setTimeout> | null = null

    function spawn() {
      setPuffs((prev) => [...prev, new SteamPuff()])
      scheduleNext()
    }
    function scheduleNext() {
      const spawnDelay = 400 + Math.random() * 500
      timeoutId = setTimeout(spawn, spawnDelay)
    }
    scheduleNext()

    return () => {
      if (timeoutId) clearTimeout(timeoutId)
    }
  }, [])

  useFrame((_, delta) => {
    setPuffs((prev) =>
      prev
        .map((puff) => {
          puff.update(delta)
          return puff
        })
        .filter((puff) => puff.isAlive())
    )
  })

  return (
    <group>
      {puffs.map((puff) => (
        <group key={puff.id} position={[puff.x, puff.y, puff.z]}>
          {puff.spheres.map((sphere, i) => {
            const alpha = puff.getOpacity()
            const scaleFactor = puff.getSphereScale(sphere.baseScale)
            return (
              <mesh
                key={i}
                position={[sphere.x, sphere.y, sphere.z]}
                scale={[scaleFactor, scaleFactor, scaleFactor]}
              >
                <sphereGeometry args={[0.5, 16, 16]} />
                <meshStandardMaterial
                  color='#fff'
                  transparent
                  opacity={alpha}
                  depthWrite={false}
                />
              </mesh>
            )
          })}
        </group>
      ))}
    </group>
  )
}

interface SoupProps {
  index: number
  z: number
  speed: number
}

function Soup({ index, z, speed }: SoupProps) {
  const ref = useRef<THREE.Group | null>(null)
  const { viewport, camera } = useThree()
  const { width, height } = viewport.getCurrentViewport(camera, [0, 0, -z])

  function getSpawnInside(width: number, height: number) {
    return {
      x: THREE.MathUtils.randFloatSpread(width),
      y: THREE.MathUtils.randFloatSpread(height),
      angle: Math.random() * Math.PI * 2
    }
  }

  function getSpawnEdgeInward(width: number, height: number) {
    const side = Math.floor(Math.random() * 4) // 0=top,1=bottom,2=left,3=right
    let x = 0
    let y = 0

    if (side === 0) {
      // top edge
      x = THREE.MathUtils.randFloatSpread(width * 2)
      y = height * 1.2
    } else if (side === 1) {
      // bottom edge
      x = THREE.MathUtils.randFloatSpread(width * 2)
      y = -height * 1.2
    } else if (side === 2) {
      // left edge
      x = -width * 1.2
      y = THREE.MathUtils.randFloatSpread(height * 2)
    } else {
      // right edge
      x = width * 1.2
      y = THREE.MathUtils.randFloatSpread(height * 2)
    }

    // Force angle to point roughly toward center (0,0).
    const angle = Math.atan2(0 - y, 0 - x)

    return { x, y, angle }
  }

  const [data, setData] = useState(() => {
    const { x, y, angle } = getSpawnInside(width, height)
    return {
      x,
      y,
      angle,
      spin: THREE.MathUtils.randFloat(1, 2),
      rX: Math.random() * Math.PI,
      rZ: Math.random() * Math.PI
    }
  })

  // Called when soup leaves the screen, to respawn on an edge inward
  function respawn() {
    const { x, y, angle } = getSpawnEdgeInward(width, height)
    setData((prev) => ({
      ...prev,
      x,
      y,
      angle,
      spin: THREE.MathUtils.randFloat(1, 2),
      rX: Math.random() * Math.PI,
      rZ: Math.random() * Math.PI
    }))
  }

  useFrame((state, dt) => {
    if (!ref.current || dt > 0.1) return

    // Move in direction of data.angle
    const moveX = Math.cos(data.angle) * speed * dt
    const moveY = Math.sin(data.angle) * speed * dt

    data.x += moveX
    data.y += moveY

    ref.current.position.set(data.x, data.y, -z)
    ref.current.rotation.set(
      (data.rX += dt / data.spin),
      Math.sin(index * 1000 + state.clock.elapsedTime / 10) * Math.PI,
      (data.rZ += dt / data.spin)
    )

    // If off-screen, respawn on a random edge traveling inward
    const offX = width * 1.3
    const offY = height * 1.3
    if (data.x < -offX || data.x > offX || data.y < -offY || data.y > offY) {
      respawn()
    }
  })

  return (
    <group ref={ref}>
      <BowlAndSoup />
      <NaturalSteam />
    </group>
  )
}

interface FloatingSoupsProps {
  speed?: number
  count?: number
  depth?: number
  easing?: (x: number) => number
}

export default function FloatingSoups({
  speed = 1,
  count = 60,
  depth = 70,
  easing = (x: number) => Math.sqrt(1 - Math.pow(x - 1, 2))
}: FloatingSoupsProps) {
  return (
    <Canvas
      flat
      gl={{ antialias: false }}
      dpr={[1, 1.5]}
      camera={{ position: [0, 0, 10], fov: 20, near: 0.01, far: depth + 15 }}
    >
      <color attach='background' args={['#ffbf40']} />
      <spotLight
        position={[10, 20, 10]}
        penumbra={1}
        decay={0}
        intensity={3}
        color='orange'
      />

      {Array.from({ length: count }, (_, i) => (
        <Soup
          key={i}
          index={i}
          z={Math.round(easing(i / count) * depth)}
          speed={speed}
        />
      ))}

      <Environment preset='sunset' />

      <EffectComposer multisampling={0} enableNormalPass={false}>
        <DepthOfField
          target={[0, 0, 60]}
          focalLength={0.4}
          bokehScale={14}
          height={700}
        />
        <ToneMapping />
      </EffectComposer>
    </Canvas>
  )
}
