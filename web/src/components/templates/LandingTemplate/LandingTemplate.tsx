import type React from 'react'
import { Box } from '@/components/atoms/Box'
import { Navbar, type NavbarProps } from '@/components/organisms/Navbar'
import { HeroSection, type HeroSectionProps } from '@/components/organisms/HeroSection'
import { FeaturesGrid, type FeaturesGridProps } from '@/components/organisms/FeaturesGrid'
import { CallToAction, type CallToActionProps } from '@/components/organisms/CallToAction'
import { Footer, type FooterProps } from '@/components/organisms/Footer'

export interface LandingTemplateProps {
  navbar?: NavbarProps
  hero?: HeroSectionProps
  features?: FeaturesGridProps
  callToAction?: CallToActionProps
  footer?: FooterProps
  children?: React.ReactNode
  className?: string
}

export const LandingTemplate: React.FC<LandingTemplateProps> = ({
  navbar,
  hero,
  features,
  callToAction,
  footer,
  children,
  className,
}) => {
  return (
    <Box
      className={['flex min-h-screen flex-col bg-background text-foreground', className]
        .filter(Boolean)
        .join(' ')}
    >
      <Navbar {...navbar} />
      <Box as="main" className="flex-1">
        {hero && <HeroSection {...hero} />}
        {features && <FeaturesGrid {...features} />}
        {children}
        {callToAction && <CallToAction {...callToAction} />}
      </Box>
      <Footer {...footer} />
    </Box>
  )
}
