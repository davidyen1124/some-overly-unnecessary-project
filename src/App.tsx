import { Component, useEffect, useState, type ReactNode } from 'react'
import FloatingSoups from './components/FloatingSoups'

class SceneBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false }
  static getDerivedStateFromError() { return { failed: true } }
  render() {
    if (this.state.failed) return (
      <div className='scene-error' role='alert'>
        <p>The soup couldn’t be served. Please try loading it again.</p>
        <button onClick={() => window.location.reload()}>Try again</button>
      </div>
    )
    return this.props.children
  }
}

function App() {
  const [closeUp, setCloseUp] = useState(false)
  const [paused, setPaused] = useState(false)
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches)
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)')
    const update = () => setReducedMotion(media.matches)
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  return (
    <main className={closeUp ? 'soup-app close-up' : 'soup-app'}>
      <SceneBoundary>
        <FloatingSoups closeUp={closeUp} paused={paused} reducedMotion={reducedMotion} />
      </SceneBoundary>
      <header className='masthead'>
        <h1>S.O.U.P.</h1>
        <p>Some Overly Unnecessary Project</p>
      </header>
      <div className='scene-caption' aria-live='polite'>
        <span>{closeUp ? 'A closer look at absolutely nothing useful.' : 'Still unnecessary. Now freshly made.'}</span>
        {closeUp && <small>Drag to orbit · Scroll or pinch to zoom</small>}
      </div>
      <nav className='controls' aria-label='Soup scene controls'>
        <button className={!closeUp ? 'selected' : ''} aria-pressed={!closeUp} onClick={() => setCloseUp(false)}>Floating soup</button>
        <button className={closeUp ? 'selected' : ''} aria-pressed={closeUp} onClick={() => setCloseUp(true)}>Close-up</button>
        <span className='control-divider' />
        <button aria-label={reducedMotion ? 'Animation disabled for reduced motion' : paused ? 'Resume animation' : 'Pause animation'} aria-pressed={paused || reducedMotion} disabled={reducedMotion} onClick={() => setPaused(!paused)}>{reducedMotion ? 'Still' : paused ? 'Play' : 'Pause'}</button>
      </nav>
      <a className='model-link' href={`${import.meta.env.BASE_URL}models/realistic-soup.glb`} download='realistic-soup.glb'>Take it to go ↗ <span>Download 3D model</span></a>
    </main>
  )
}
export default App
