import { LandingTemplate } from '@/components/templates/LandingTemplate'
import { Box } from '@/components/atoms/Box'
import { Stack } from '@/components/atoms/Stack'
import { Text } from '@/components/atoms/Text'
import { Heading } from '@/components/atoms/Heading'
import { StatCard } from '@/components/molecules/StatCard'

const FEATURES = [
  {
    id: 'pipeline',
    icon: 'documentation-icon',
    title: 'Pipeline de donnees',
    description:
      'Nettoyage, tokenisation et splitting de votre corpus avec des controles de qualite integres.',
  },
  {
    id: 'training',
    icon: 'social-icon',
    title: 'Entrainement supervise',
    description:
      'Lancez vos runs Transformers, suivez les metriques en temps reel et comparez les versions.',
  },
  {
    id: 'inference',
    icon: 'github-icon',
    title: 'Inference souple',
    description:
      'Deployez vos checkpoints et servez des requetes via une API typee et securisee.',
  },
  {
    id: 'dashboard',
    icon: 'discord-icon',
    title: 'Tableau de bord',
    description:
      'Visualisez vos runs, vos couts et la sante de vos modeles depuis une interface unique.',
  },
  {
    id: 'collab',
    icon: 'x-icon',
    title: 'Collaboration',
    description: 'Partagez vos experiments et vos datasets avec toute votre equipe.',
  },
  {
    id: 'quality',
    icon: 'bluesky-icon',
    title: 'Qualite & tests',
    description: 'Suite de tests automatiques et criteres d’acceptation pour chaque livraison.',
  },
]

function App() {
  return (
    <LandingTemplate
      navbar={{
        brand: 'Riah Code',
        badge: 'Beta',
        links: [
          { label: 'Fonctionnalites', href: '#features', isActive: true },
          { label: 'Documentation', href: '#docs' },
          { label: 'Tarifs', href: '#pricing' },
        ],
        actions: [
          { label: 'Connexion', variant: 'ghost' },
          { label: 'Commencer', variant: 'primary' },
        ],
      }}
      hero={{
        badge: 'Nouveau : fine-tuning en 1 clic',
        title: 'Entrainez vos modeles de langage, sans friction',
        subtitle:
          'Riah Code est la plateforme complete pour preparer vos donnees, entrainer vos Transformers et deployer votre inference depuis un seul tableau de bord.',
        primaryAction: { label: 'Commencer gratuitement' },
        secondaryAction: { label: 'Lire la documentation', variant: 'outline' },
      }}
      features={{
        eyebrow: 'Plateforme',
        title: 'Tout ce qu’il faut pour vos modeles',
        subtitle: 'De la preparation du corpus au deploiement, un pipeline complet et unifie.',
        columns: 3,
        items: FEATURES,
      }}
      callToAction={{
        title: 'Pret a lancer votre premier run ?',
        description:
          'Creez un compte, importez votre corpus et demarrez un entrainement en quelques minutes.',
        primaryAction: { label: 'Commencer gratuitement' },
        secondaryAction: { label: 'Voir une demo', variant: 'outline' },
        note: 'Sans carte bancaire — annulable a tout moment.',
      }}
      footer={{
        brand: 'Riah Code',
        tagline: 'La plateforme dentrainement et dinference pour vos modeles de langage.',
        columns: [
          {
            id: 'produit',
            title: 'Produit',
            links: [
              { label: 'Fonctionnalites', href: '#features' },
              { label: 'Tarifs', href: '#pricing' },
              { label: 'Changelog', href: '#changelog' },
            ],
          },
          {
            id: 'ressources',
            title: 'Ressources',
            links: [
              { label: 'Documentation', href: '#docs' },
              { label: 'Guide API', href: '#api' },
              { label: 'Blog', href: '#blog' },
            ],
          },
          {
            id: 'entreprise',
            title: 'Entreprise',
            links: [
              { label: 'A propos', href: '#about' },
              { label: 'Contact', href: '#contact' },
              { label: 'Mentions legales', href: '#legal' },
            ],
          },
        ],
        socialLinks: [
          { label: 'GitHub', href: 'https://github.com' },
          { label: 'X', href: 'https://x.com' },
          { label: 'Discord', href: 'https://discord.com' },
        ],
      }}
    >
      <Box as="section" className="border-b border-border bg-muted/30 px-4 py-16 sm:px-6 lg:px-8">
        <Stack align="center" spacing="sm" className="mx-auto mb-10 max-w-2xl text-center">
          <Heading level={2} size="2xl" weight="bold" color="default">
            Une plateforme, toutes les etapes
          </Heading>
          <Text size="lg" color="muted">
            Des chiffres concrets issus de nos utilisateurs durant la beta fermee.
          </Text>
        </Stack>
        <Box className="mx-auto grid max-w-6xl grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Runs entraines"
            value="12 480"
            badge={{ variant: 'accent', label: 'Live' }}
            trend={{ value: '+18 % ce mois', isPositive: true }}
          />
          <StatCard
            title="Tokens traites"
            value="3,2 Md"
            badge={{ variant: 'muted', label: 'Corpus' }}
            trend={{ value: '+9 % ce mois', isPositive: true }}
          />
          <StatCard
            title="Latence moyenne"
            value="142 ms"
            badge={{ variant: 'success', label: 'Sain' }}
            trend={{ value: '-12 % ce mois', isPositive: true }}
          />
          <StatCard
            title="Cout par run"
            value="0,42 €"
            badge={{ variant: 'warning', label: 'Budget' }}
            trend={{ value: '+3 % ce mois', isPositive: false }}
          />
        </Box>
      </Box>
    </LandingTemplate>
  )
}

export default App
