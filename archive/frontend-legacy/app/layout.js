import "./globals.css";
import ClientProviders from "@/components/ClientProviders";

export const metadata = {
  title: "Project Seed | AI Prediction Markets",
  description: "Bet on the future. Watch AI agents trade on simulated realities.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen text-white antialiased">
        <ClientProviders>
          {children}
        </ClientProviders>
      </body>
    </html>
  );
}