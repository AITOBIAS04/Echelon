// This line tells Next.js that this is a "Client Component"
// which means it can run in the browser and fetch data.
"use client";

// We import two "hooks" from React
import { useState, useEffect } from "react";

export default function Home() {
  
  // We set up "state" variables to hold our data
  const [message, setMessage] = useState("Loading...");
  const [error, setError] = useState(null);

  // This "useEffect" hook runs once when the page loads
  useEffect(() => {
    
    // We define a function to fetch data from our API
    async function getRootMessage() {
      try {
        // This is the "bridge"! We are fetching from our backend.
        const res = await fetch("http://localhost:8000/");
        
        if (!res.ok) {
          throw new Error("Failed to fetch data from backend");
        }
        
        const data = await res.json();
        setMessage(data.message); // Set the message from the API
      } catch (err) {
        setError(err.message);
      }
    }

    // Call the function
    getRootMessage();

  }, []); // The empty array [] means "only run this once"

  // This is the HTML (JSX) that gets rendered
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">AI Marketplace</h1>
        <p className="text-xl">
          {/* We display the message from the backend here */}
          {error ? `Error: ${error}` : message}
        </p>
      </div>
    </main>
  );
}