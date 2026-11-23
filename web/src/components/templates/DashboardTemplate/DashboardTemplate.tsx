import type React from "react";
import { Box } from "@/components/atoms/Box";
import { Navbar, type NavbarProps } from "@/components/organisms/Navbar";
import {
  PageHeader,
  type PageHeaderProps,
} from "@/components/organisms/PageHeader";

export interface DashboardTemplateProps {
  header?: PageHeaderProps;
  children?: React.ReactNode;
  className?: string;
  refresh?: () => void;
}

export const DashboardTemplate: React.FC<DashboardTemplateProps> = ({
  header,
  children,
  className,
  refresh,
}) => {
  const navbar: NavbarProps = {
    brand: "Riah Code",
    badge: "Corpus",
    links: [
      { label: "Accueil", href: "/" },
      { label: "Corpus", href: "/corpus", isActive: true },
      { label: "Entrainement", href: "/training" },
      { label: "Inference", href: "/inference" },
    ],
    actions: [{ label: "Actualiser", variant: "ghost", onClick: refresh }],
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
      <Box as="main" className="flex-1 w-full">
        {header && <PageHeader {...header} />}
        <Box className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </Box>
      </Box>
    </Box>
  );
};
