import type React from "react";
import { Box } from "@/components/atoms/Box";
import { Navbar, type NavbarProps } from "@/components/organisms/Navbar";
import {
  HeroSection,
  type HeroSectionProps,
} from "@/components/organisms/HeroSection";
import {
  FeaturesGrid,
  type FeaturesGridProps,
} from "@/components/organisms/FeaturesGrid";
import {
  CallToAction,
  type CallToActionProps,
} from "@/components/organisms/CallToAction";
import { Footer, type FooterProps } from "@/components/organisms/Footer";

export interface LandingTemplateProps {
  hero?: HeroSectionProps;
  features?: FeaturesGridProps;
  callToAction?: CallToActionProps;
  footer?: FooterProps;
  children?: React.ReactNode;
  className?: string;
}

export const LandingTemplate: React.FC<LandingTemplateProps> = ({
  hero,
  features,
  callToAction,
  footer,
  children,
  className,
}) => {
  const navbar: NavbarProps = {
    brand: "Riah Code",
    badge: "Beta",
    links: [
      { label: "Corpus", href: "/corpus", isActive: true },
      { label: "Chat", href: "/chat" },
      { label: "Dashboard", href: "/dashboard" },
    ],
    actions: [
      { label: "Connexion", variant: "ghost" },
      { label: "Commencer", variant: "primary" },
    ],
  };
  
  return (
    <Box
      className={[
        "flex min-h-screen flex-col bg-background text-foreground",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
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
  );
};
