import { LandingPage } from "@/pages/LandingPage";
import { CorpusPage } from "@/pages/CorpusPage";
import { Box } from "@/components/atoms/Box";
import { BrowserRouter, Route, Routes } from "react-router-dom";

function App() {
  return (
    <Box className="min-h-screen bg-background text-foreground">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/corpus" element={<CorpusPage />} />
        </Routes>
      </BrowserRouter>
    </Box>
  );
}

export default App;
