import NextAuth, { type NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import axios from 'axios'; // Added axios for API calls

// (Removed unused verifyCredentials function)

const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      // The name to display on the sign-in form (e.g., "Sign in with...")
      name: 'Credentials',
      // The credentials is used to generate a suitable form on the sign-in page.
      // You can specify whatever fields you are expecting to be submitted.
      // e.g., domain, username, password, 2FA token, etc.
      // You can pass any HTML attribute to the <input> tag through the object.
      credentials: {
        email: {
          label: 'Email',
          type: 'email',
          placeholder: 'john.doe@example.com',
        },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        console.log(
          '[NextAuth Authorize] Called with credentials:',
          JSON.stringify(credentials),
        );

        if (!credentials?.email || !credentials?.password) {
          console.error('[NextAuth Authorize] Email or password missing.');
          throw new Error('Email and password are required.');
        }

        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
        if (!apiBaseUrl) {
          console.error(
            '[NextAuth Authorize] NEXT_PUBLIC_API_BASE_URL is not set',
          );
          throw new Error('API base URL is not configured.');
        }
        console.log('[NextAuth Authorize] API Base URL:', apiBaseUrl);

        try {
          const formData = new URLSearchParams();
          formData.append('email', credentials.email);
          formData.append('password', credentials.password);
          console.log(
            '[NextAuth Authorize] Attempting to login to backend with email:',
            credentials.email,
          );

          const response = await axios.post(
            `${apiBaseUrl}/users/login`,
            formData,
            {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            },
          );
          console.log(
            '[NextAuth Authorize] Backend /users/login response status:',
            response.status,
          );
          console.log(
            '[NextAuth Authorize] Backend /users/login response data:',
            JSON.stringify(response.data),
          );

          const backendData = response.data;

          if (response.status === 200 && backendData.access_token) {
            console.log(
              '[NextAuth Authorize] Login successful, received access_token:',
              backendData.access_token,
            );

            let userProfile = {
              id: '',
              email: credentials.email,
              name: '',
              role: '', // Initialize role, will be overwritten
            };
            console.log(
              '[NextAuth Authorize] Attempting to fetch /users/me with token.',
            );

            try {
              const profileResponse = await axios.get(
                `${apiBaseUrl}/users/me`,
                {
                  headers: {
                    Authorization: `Bearer ${backendData.access_token}`,
                  },
                },
              );
              console.log(
                '[NextAuth Authorize] Backend /users/me response status:',
                profileResponse.status,
              );
              console.log(
                '[NextAuth Authorize] Backend /users/me response data:',
                JSON.stringify(profileResponse.data),
              );

              if (profileResponse.data) {
                userProfile = {
                  id: profileResponse.data.id,
                  email: profileResponse.data.email,
                  name:
                    profileResponse.data.full_name ||
                    profileResponse.data.email,
                  // Rolle aus roles-Liste extrahieren (z.B. erstes Element)
                  role: Array.isArray(profileResponse.data.roles) && profileResponse.data.roles.length > 0
                    ? profileResponse.data.roles[0]
                    : undefined,
                };
                console.log(
                  '[NextAuth Authorize] User profile constructed:',
                  JSON.stringify(userProfile),
                );
              }
            } catch (profileError: unknown) {
              let message = 'Unknown error';
              if (
                profileError &&
                typeof profileError === 'object' &&
                'message' in profileError &&
                typeof (profileError as { message?: string }).message ===
                  'string'
              ) {
                message = (profileError as { message: string }).message;
              }
              console.error(
                '[NextAuth Authorize] Error fetching user profile:',
                (profileError as { response?: { data?: unknown } }).response
                  ?.data || message,
              );
              if (!userProfile.name) userProfile.name = userProfile.email;
              if (!userProfile.id) {
                console.error(
                  '[NextAuth Authorize] User ID is missing after profile fetch attempt.',
                );
              }
            }

            const finalUserObject = {
              ...userProfile,
              accessToken: backendData.access_token,
            };
            console.log(
              '[NextAuth Authorize] Returning user object to NextAuth:',
              JSON.stringify(finalUserObject),
            );
            return finalUserObject;
          } else {
            console.warn(
              '[NextAuth Authorize] Login to backend failed or no access_token. Status:',
              response.status,
              'Data:',
              JSON.stringify(backendData),
            );
            return null;
          }
        } catch (error: unknown) {
          let message = 'Unknown error';
          if (
            error &&
            typeof error === 'object' &&
            'message' in error &&
            typeof (error as { message?: string }).message === 'string'
          ) {
            message = (error as { message: string }).message;
          }
          console.error('[NextAuth Authorize] RAW ERROR OBJECT:', error);
          if (
            error &&
            typeof error === 'object' &&
            'response' in error &&
            typeof (
              error as {
                response?: {
                  data?: unknown;
                  status?: number;
                  headers?: unknown;
                };
              }
            ).response === 'object'
          ) {
            const response = (
              error as {
                response?: {
                  data?: unknown;
                  status?: number;
                  headers?: unknown;
                };
              }
            ).response;
            if (response) {
              console.error(
                '[NextAuth Authorize] Axios error response data:',
                JSON.stringify(response.data),
              );
              console.error(
                '[NextAuth Authorize] Axios error response status:',
                response.status,
              );
              console.error(
                '[NextAuth Authorize] Axios error response headers:',
                JSON.stringify(response.headers),
              );
            }
          } else if (error && typeof error === 'object' && 'request' in error) {
            // Axios error where request was made but no response received
            console.error(
              '[NextAuth Authorize] Axios error: No response received. Request details:',
              (error as { request?: unknown }).request,
            );
          } else {
            // Something else happened in setting up the request that triggered an Error
            console.error(
              '[NextAuth Authorize] Non-Axios error or setup issue:',
              message,
            );
          }
          let errorMessage: string = 'Unknown error';
          if (
            error &&
            typeof error === 'object' &&
            'response' in error &&
            typeof (error as { response?: { data?: { detail?: string } } })
              .response === 'object'
          ) {
            const detail = (
              error as { response?: { data?: { detail?: string } } }
            ).response?.data?.detail;
            if (typeof detail === 'string' && detail) {
              errorMessage = detail;
            } else if (typeof message === 'string' && message) {
              errorMessage = message;
            } else {
              errorMessage =
                'Invalid credentials or server error due to frontend issue.';
            }
          } else if (typeof message === 'string' && message) {
            errorMessage = message;
          }
          console.error(
            '[NextAuth Authorize] Final error message to be thrown:',
            errorMessage,
          );
          throw new Error(errorMessage);
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user, account }) {
      // Persist the access token to the JWT right after signin
      if (account && user) {
        // `user` is the object returned from authorize, `account` has provider info
        type UserWithAccessTokenAndRole = {
          accessToken?: string;
          id?: string;
          role?: string;
        };
        token.accessToken = (user as UserWithAccessTokenAndRole).accessToken;
        token.id = (user as UserWithAccessTokenAndRole).id; // Ensure user id is in the token
        token.role = (user as UserWithAccessTokenAndRole).role; // <<< ADDED ROLE TO TOKEN
        // token.refreshToken = (user as UserWithAccessTokenAndRole).refreshToken; // If using refresh tokens
      }
      return token;
    },
    async session({ session, token }) {
      // Send properties to the client, like an access_token and user id from a provider.
      type UserWithAccessTokenAndRole = {
        accessToken?: string;
        id?: string;
        role?: string;
      };
      (session.user as UserWithAccessTokenAndRole).accessToken =
        token.accessToken as string | undefined;
      (session.user as UserWithAccessTokenAndRole).id = token.id as
        | string
        | undefined; // Add id to session user object
      (session.user as UserWithAccessTokenAndRole).role = token.role as
        | string
        | undefined; // <<< ADDED ROLE TO SESSION USER
      return session;
    },
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
