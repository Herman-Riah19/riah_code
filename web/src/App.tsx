import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { CorpusPage } from '@/pages/CorpusPage'
import { DashboardTemplate } from '@/components/templates/DashboardTemplate'
import { Box } from '@/components/atoms/Box'
import { Text } from '@/components/atoms/Text'

function HomeContent() {
  return (
    <Box className="p-4">
      <Text size="md" color="muted">
        Bienvenue sur Riah Code - Plateforme d entrainement et d inference
      </Text>
    </Box>
  )
}

function TrainingContent() {
  return (
    <Box className="p-4">
      <Text size="md" color="muted">
        Page Entrainement - bientot disponible
      </Text>
    </Box>
  )
}

function InferenceContent() {
  return (
    <Box className="p-4">
      <Text size="md" color="muted">
        Page Inference - bientot disponible
      </Text>
    </Box>
  )
}

function App() {
  return (
    <BrowserRouter>
      <DashboardTemplate brand="Riah Code">
        <Routes>
          <Route path="/" element={<HomeContent />} />
          <Route path="/corpus" element={<CorpusPage />} />
          <Route path="/training" element={<TrainingContent />} />
          <Route path="/inference" element={<InferenceContent />} />
        </Routes>
      </DashboardTemplate>
    </BrowserRouter>
  )
}

export default App