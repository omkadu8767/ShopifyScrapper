/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f5f7ff',
                    100: '#ebf0ff',
                    200: '#d6e0ff',
                    300: '#b8c9ff',
                    400: '#8fa6ff',
                    500: '#667eea',
                    600: '#5568d3',
                    700: '#4553b8',
                    800: '#3a4696',
                    900: '#2e3775',
                },
                secondary: {
                    50: '#faf5ff',
                    100: '#f3e8ff',
                    200: '#e9d5ff',
                    300: '#d8b4fe',
                    400: '#c084fc',
                    500: '#764ba2',
                    600: '#653d8c',
                    700: '#553276',
                    800: '#452860',
                    900: '#36204b',
                }
            }
        },
    },
    plugins: [],
}
