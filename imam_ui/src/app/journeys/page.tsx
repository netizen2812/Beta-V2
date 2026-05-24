import { redirect } from 'next/navigation';

// Journeys are now embedded in the main page as a horizontal scroll section.
// This page redirects home so any direct link still works gracefully.
export default function JourneysRedirectPage() {
  redirect('/');
}
