import { Navbar } from "@/components/layout/Navbar";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex-1 flex flex-col items-center justify-center">
        {/* Placeholder for the rest of the design */}
        <p className="text-gray-400">Content pending...</p>
      </div>
    </main>
  );
}
