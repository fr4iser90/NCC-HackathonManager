'use client';

import { Suspense } from 'react';
import ErrorForm from './ErrorForm';

export default function AuthErrorPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ErrorForm />
    </Suspense>
  );
}
