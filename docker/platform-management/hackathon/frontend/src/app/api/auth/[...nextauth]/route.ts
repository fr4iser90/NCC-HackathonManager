import NextAuth, { type NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import axios from 'axios'; // Added axios for API calls

// Placeholder for a function to verify credentials against your database or backend API
// In a real application, this would involve hashing passwords and comparing them securely.
async function verifyCredentials(credentials: Record<string, string> | undefined) {
  // IMPORTANT: Replace this with actual credential verification logic
  // This is a mock implementation for demonstration purposes.
  if (credentials?.email === 'user@example.com' && credentials?.password === 'password') {
    // Return user object if credentials are valid
    // The 'id' property is important for NextAuth.js session management.
    // You can include other user properties as needed.
    return { id: '1', name: 'Test User', email: 'user@example.com' };
  }
  // Return null if credentials are not valid
  return null;
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      // The name to display on the sign-in form (e.g., "Sign in with...")
      name: 'Credentials',
      // The credentials is used to generate a suitable form on the sign-in page.
      // You can specify whatever fields you are expecting to be submitted.
      // e.g., domain, username, password, 2FA token, etc.
      // You can pass any HTML attribute to the <input> tag through the object.
      credentials: {
        email: { label: "Email", type: "email", placeholder: "john.doe@example.com" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials, req) {
        console.log("[NextAuth Authorize] Called with credentials:", JSON.stringify(credentials));

        if (!credentials?.email || !credentials?.password) {
          console.error("[NextAuth Authorize] Email or password missing.");
          throw new Error("Email and password are required.");
        }

        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
        if (!apiBaseUrl) {
          console.error("[NextAuth Authorize] NEXT_PUBLIC_API_BASE_URL is not set");
          throw new Error("API base URL is not configured.");
        }
        console.log("[NextAuth Authorize] API Base URL:", apiBaseUrl);

        try {
          const formData = new URLSearchParams();
          formData.append('email', credentials.email);
          formData.append('password', credentials.password);
          console.log("[NextAuth Authorize] Attempting to login to backend with email:", credentials.email);

          const response = await axios.post(`${apiBaseUrl}/users/login`, formData, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          });
          console.log("[NextAuth Authorize] Backend /users/login response status:", response.status);
          console.log("[NextAuth Authorize] Backend /users/login response data:", JSON.stringify(response.data));

          const backendData = response.data;

          if (response.status === 200 && backendData.access_token) {
            console.log("[NextAuth Authorize] Login successful, received access_token:", backendData.access_token);
            
            let userProfile = {
              id: '', 
              email: credentials.email, 
              name: '',
              role: '' // Initialize role, will be overwritten
            };
            console.log("[NextAuth Authorize] Attempting to fetch /users/me with token.");

            try {
              const profileResponse = await axios.get(`${apiBaseUrl}/users/me`, {
                headers: {
                  'Authorization': `Bearer ${backendData.access_token}`
                }
              });
              console.log("[NextAuth Authorize] Backend /users/me response status:", profileResponse.status);
              console.log("[NextAuth Authorize] Backend /users/me response data:", JSON.stringify(profileResponse.data));

              if (profileResponse.data) {
                userProfile = {
                  id: profileResponse.data.id, 
                  email: profileResponse.data.email,
                  name: profileResponse.data.full_name || profileResponse.data.email,
                  role: profileResponse.data.role // <<< ROLE HERE
                };
                console.log("[NextAuth Authorize] User profile constructed:", JSON.stringify(userProfile));
              }
            } catch (profileError: any) {
              console.error("[NextAuth Authorize] Error fetching user profile:", profileError.response?.data || profileError.message);
              if (!userProfile.name) userProfile.name = userProfile.email;
              if (!userProfile.id) {
                 console.error("[NextAuth Authorize] User ID is missing after profile fetch attempt.");
              }
            }
            
            const finalUserObject = {
              ...userProfile,
              accessToken: backendData.access_token,
            };
            console.log("[NextAuth Authorize] Returning user object to NextAuth:", JSON.stringify(finalUserObject));
            return finalUserObject;
          } else {
            console.warn("[NextAuth Authorize] Login to backend failed or no access_token. Status:", response.status, "Data:", JSON.stringify(backendData));
            return null; 
          }
        } catch (error: any) {
          console.error("[NextAuth Authorize] RAW ERROR OBJECT:", error);
          if (error.response) {
            // Axios error with response from server
            console.error("[NextAuth Authorize] Axios error response data:", JSON.stringify(error.response.data));
            console.error("[NextAuth Authorize] Axios error response status:", error.response.status);
            console.error("[NextAuth Authorize] Axios error response headers:", JSON.stringify(error.response.headers));
          } else if (error.request) {
            // Axios error where request was made but no response received
            console.error("[NextAuth Authorize] Axios error: No response received. Request details:", error.request);
          } else {
            // Something else happened in setting up the request that triggered an Error
            console.error("[NextAuth Authorize] Non-Axios error or setup issue:", error.message);
          }
          const errorMessage = error.response?.data?.detail || error.message || "Invalid credentials or server error due to frontend issue.";
          console.error("[NextAuth Authorize] Final error message to be thrown:", errorMessage);
          throw new Error(errorMessage);
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      // Persist the access token to the JWT right after signin
      if (account && user) { // `user` is the object returned from authorize, `account` has provider info
        token.accessToken = (user as any).accessToken;
        token.id = (user as any).id; // Ensure user id is in the token
        token.role = (user as any).role; // <<< ADDED ROLE TO TOKEN
        // token.refreshToken = (user as any).refreshToken; // If using refresh tokens
      }
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client, like an access_token and user id from a provider.
      (session.user as any).accessToken = token.accessToken;
      (session.user as any).id = token.id; // Add id to session user object
      (session.user as any).role = token.role; // <<< ADDED ROLE TO SESSION USER
      return session;
    }
  },
  pages: {
    signIn: '/auth/signin', // Using a custom sign-in page path (we'll create this later)
    error: '/auth/error', // Displaying errors on a custom error page
  },
  session: {
    strategy: 'jwt',
  },
  secret: process.env.NEXTAUTH_SECRET,
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST }; 