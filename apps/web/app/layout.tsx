import type { Metadata } from "next";
import "./styles.css";
import "./workspace.css";

export const metadata: Metadata = {title: "DeployPilot", description: "Self-healing delivery control plane"};

export default function Layout({children}: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
