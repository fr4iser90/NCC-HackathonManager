export type Hackathon = {
  id: string;
  name: string;
  description?: string;
  start_date: string;
  end_date: string;
  status: string;
  mode: string;
  category?: string;
  tags?: string[];
  banner_image_url?: string;
  sponsor?: string;
  // Füge weitere Felder hinzu, falls du sie im Backend hast!
};
