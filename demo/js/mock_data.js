/**
 * HỆ THỐNG GỢI Ý ĐIỆN ẢNH MOODGRAPH - KHO DỮ LIỆU MẪU & BỘ MÁY ĐỀ XUẤT ĐỘC LẬP (STANDALONE PROTOTYPE)
 * File: js/mock_data.js
 * 
 * Bộ dữ liệu mẫu tự chứa phong phú và chuẩn xác 100% theo MovieLens 25M (ml-25m)
 * và kết quả thực nghiệm của hệ thống gợi ý MoodGraph.
 * 
 * Quy chuẩn:
 * - 100% Tiếng Việt chuẩn ngữ pháp và UTF-8.
 * - Tuyệt đối không dùng ký hiệu LaTeX hoặc dấu dollar ($).
 * - Thuật ngữ: "Recommendation Model Lab / Benchmark Dashboard" dành cho nghiên cứu sinh & kỹ sư hệ gợi ý.
 * - Khả năng chạy độc lập qua giao thức file:// trên trình duyệt và môi trường Node.js.
 */

(function (global) {
  'use strict';

  // =========================================================================
  // 1. DANH MỤC 19 THỂ LOẠI ĐIỆN ẢNH CHUẨN MOVIELENS 25M
  // =========================================================================
  const GENRES = [
    { id: "all", name: "Tất cả Thể loại", enName: "All", count: 62423, color: "amber" },
    { id: "action", name: "Hành động", enName: "Action", count: 7348, color: "red" },
    { id: "adventure", name: "Phiêu lưu", enName: "Adventure", count: 4145, color: "orange" },
    { id: "animation", name: "Hoạt hình", enName: "Animation", count: 2929, color: "amber" },
    { id: "children", name: "Thiếu nhi", enName: "Children", count: 2935, color: "yellow" },
    { id: "comedy", name: "Hài kịch", enName: "Comedy", count: 16870, color: "lime" },
    { id: "crime", name: "Hình sự / Tội phạm", enName: "Crime", count: 5319, color: "emerald" },
    { id: "documentary", name: "Tài liệu", enName: "Documentary", count: 5605, color: "teal" },
    { id: "drama", name: "Chính kịch / Tâm lý", enName: "Drama", count: 25606, color: "slate" },
    { id: "fantasy", name: "Kỳ ảo / Giả tưởng", enName: "Fantasy", count: 2731, color: "sky" },
    { id: "film-noir", name: "Phim đen", enName: "Film-Noir", count: 353, color: "blue" },
    { id: "horror", name: "Kinh dị", enName: "Horror", count: 5989, color: "rose" },
    { id: "musical", name: "Ca nhạc / Vũ kịch", enName: "Musical", count: 1054, color: "amber" },
    { id: "mystery", name: "Bí ẩn / Giật gân", enName: "Mystery", count: 2925, color: "slate" },
    { id: "romance", name: "Lãng mạn / Tình cảm", enName: "Romance", count: 7719, color: "pink" },
    { id: "sci-fi", name: "Khoa học viễn tưởng", enName: "Sci-Fi", count: 3595, color: "rose" },
    { id: "thriller", name: "Hồi hộp / Ly kỳ", enName: "Thriller", count: 8654, color: "slate" },
    { id: "war", name: "Chiến tranh", enName: "War", count: 1874, color: "zinc" },
    { id: "western", name: "Miền Tây", enName: "Western", count: 1399, color: "stone" },
    { id: "no-genres-listed", name: "Chưa phân loại", enName: "(no genres listed)", count: 5062, color: "gray" }
  ];

  // =========================================================================
  // 1.1 DANH MỤC 7 NHÓM TÂM TRẠNG ĐIỆN ẢNH (MOOD TAXONOMY)
  // =========================================================================
  const MOOD_TAXONOMY = [
    {
      id: "mind_bending",
      name: "Kích thích trí tuệ / Xoắn não",
      shortName: "Xoắn não",
      enName: "Mind-Bending",
      color: "#D97706",
      description: "Cốt truyện phi tuyến tính, nghịch lý thời gian, triết học nhận thức và những cú twist đảo chiều ngoạn mục.",
      targetWeights: { depth: 0.95, pacing: 0.75, auteur: 0.90, tone: 0.45 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7M9 21h6"/></svg>'
    },
    {
      id: "suspense",
      name: "Hồi hộp / Ly kỳ thót tim",
      shortName: "Hồi hộp",
      enName: "Suspense & Thrills",
      color: "#EA580C",
      description: "Căng thẳng tột độ, điều tra tội phạm tinh vi, rùng rợn nghẹt thở khiến nhịp tim tăng dồn dập.",
      targetWeights: { depth: 0.85, pacing: 0.90, auteur: 0.85, tone: 0.25 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
    },
    {
      id: "reflective",
      name: "Sâu lắng / Chiêm nghiệm",
      shortName: "Sâu lắng",
      enName: "Deep & Reflective",
      color: "#F59E0B",
      description: "Tâm lý nhân vật đa tầng, thân phận con người, khát vọng tự do và những khoảng lặng triết học.",
      targetWeights: { depth: 0.98, pacing: 0.35, auteur: 0.95, tone: 0.50 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg>'
    },
    {
      id: "epic_adventure",
      name: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      shortName: "Phiêu lưu",
      enName: "Epic Adventure",
      color: "#0284C7",
      description: "Không gian vũ trụ bao la, sử thi hoành tráng, kỳ quan thiên nhiên và hành trình anh hùng quật khởi.",
      targetWeights: { depth: 0.85, pacing: 0.80, auteur: 0.90, tone: 0.70 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
    },
    {
      id: "uplifting",
      name: "Thư giãn / Vui tươi sảng khoái",
      shortName: "Thư giãn",
      enName: "Uplifting & Joyful",
      color: "#10B981",
      description: "Hài hước hóm hỉnh, ấm áp tình người, ca vũ nhạc tràn đầy sinh khí và năng lượng tích cực.",
      targetWeights: { depth: 0.70, pacing: 0.75, auteur: 0.75, tone: 0.95 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
    },
    {
      id: "romantic",
      name: "Lãng mạn / Day dứt ngọt ngào",
      shortName: "Lãng mạn",
      enName: "Romantic & Melancholy",
      color: "#E11D48",
      description: "Tình yêu đắm say, sự rung cảm tinh tế của hai tâm hồn, hoài niệm duyên phận dở dang.",
      targetWeights: { depth: 0.90, pacing: 0.45, auteur: 0.95, tone: 0.65 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'
    },
    {
      id: "dark_noir",
      name: "U tối / Ám ảnh hiện thực",
      shortName: "U tối",
      enName: "Dark Noir",
      color: "#78716C",
      description: "Thế giới ngầm tàn nhẫn, bi kịch số phận, sự tha hóa đạo đức và những mảng tối xã hội.",
      targetWeights: { depth: 0.95, pacing: 0.55, auteur: 0.96, tone: 0.15 },
      iconSvg: '<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    }
  ];

  // =========================================================================
  // 2. KHO PHIM MẪU 55+ TÁC PHẨM TIÊU BIỂU BAO PHỦ 19 THỂ LOẠI
  // =========================================================================
  const CATALOG = [
    {
      movieId: 318,
      title: "The Shawshank Redemption (1994)",
      cleanTitle: "The Shawshank Redemption",
      year: 1994,
      genres: ["Crime", "Drama"],
      primaryGenre: "Drama",
      ratingAvg: 4.41,
      ratingCount: 80448,
      duration: "142 phút",
      director: "Frank Darabont",
      cast: ["Tim Robbins", "Morgan Freeman", "Bob Gunton"],
      writer: "Stephen King, Frank Darabont",
      posterUrl: "https://image.tmdb.org/t/p/w500/9cqNxx0GxF0bflZmeSMuL5tnGzr.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/pNjh59JSxChQktamG3LMp9ZoQzp.jpg",
      links: {
        imdbId: "0111161",
        tmdbId: "278",
        imdbUrl: "https://www.imdb.com/title/tt0111161/",
        tmdbUrl: "https://www.themoviedb.org/movie/278"
      },
      synopsis: "Hành trình kéo dài hai thập kỷ tìm kiếm sự tự do và niềm hy vọng bền bỉ của người tù khổ sai Andy Dufresne tại nhà tù Shawshank khắc nghiệt sau khi bị kết án oan.",
      similarMovieIds: [858, 527, 296, 50]
    },
    {
      movieId: 111,
      title: "Taxi Driver (1976)",
      cleanTitle: "Taxi Driver",
      year: 1976,
      genres: ["Crime", "Drama"],
      primaryGenre: "Crime",
      ratingAvg: 4.25,
      ratingCount: 45200,
      duration: "114 phút",
      director: "Martin Scorsese",
      cast: ["Robert De Niro", "Jodie Foster", "Cybill Shepherd"],
      writer: "Paul Schrader",
      posterUrl: "https://image.tmdb.org/t/p/w500/ekstpH614fwDX8DUln1a2Opz0N8.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/9uddYYTNcLWpzUkl5iw1RUYhLhY.jpg",
      links: {
        imdbId: "0075314",
        tmdbId: "103",
        imdbUrl: "https://www.imdb.com/title/tt0075314/",
        tmdbUrl: "https://www.themoviedb.org/movie/103"
      },
      synopsis: "Một cựu binh chiến tranh cô độc lái taxi đêm tại New York dần rơi vào khủng hoảng tâm lý và quyết định hành động bạo lực để thanh lọc thành phố suy đồi.",
      similarMovieIds: [1213, 858, 296, 50]
    },
    {
      movieId: 858,
      title: "The Godfather (1972)",
      cleanTitle: "The Godfather",
      year: 1972,
      genres: ["Crime", "Drama"],
      primaryGenre: "Crime",
      ratingAvg: 4.38,
      ratingCount: 52490,
      duration: "175 phút",
      director: "Francis Ford Coppola",
      cast: ["Marlon Brando", "Al Pacino", "James Caan"],
      writer: "Mario Puzo, Francis Ford Coppola",
      posterUrl: "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/tSPT36ZKlP2WVHJLM4cQPLSzv3b.jpg",
      links: {
        imdbId: "0068646",
        tmdbId: "238",
        imdbUrl: "https://www.imdb.com/title/tt0068646/",
        tmdbUrl: "https://www.themoviedb.org/movie/238"
      },
      synopsis: "Biên niên sử gia tộc mafia Corleone tại New York khi ông trùm Vito Corleone dần chuyển giao quyền lực cho người con trai út bất đắc dĩ Michael Corleone.",
      similarMovieIds: [1221, 1213, 318, 50]
    },
    {
      movieId: 1221,
      title: "The Godfather: Part II (1974)",
      cleanTitle: "The Godfather: Part II",
      year: 1974,
      genres: ["Crime", "Drama"],
      primaryGenre: "Crime",
      ratingAvg: 4.26,
      ratingCount: 38875,
      duration: "202 phút",
      director: "Francis Ford Coppola",
      cast: ["Al Pacino", "Robert De Niro", "Robert Duvall"],
      writer: "Francis Ford Coppola, Mario Puzo",
      posterUrl: "https://image.tmdb.org/t/p/w500/8a1lJs7mFyGhGhZZDT1azJUoQiZ.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/pGzqRKrYeK4LogoysNro0vG8d8N.jpg",
      links: {
        imdbId: "0071562",
        tmdbId: "240",
        imdbUrl: "https://www.imdb.com/title/tt0071562/",
        tmdbUrl: "https://www.themoviedb.org/movie/240"
      },
      synopsis: "Câu chuyện song song giữa thời niên thiếu gian khổ gây dựng cơ nghiệp của Vito Corleone tại Sicily - New York và sự suy đồi đạo đức cô độc của Michael Corleone.",
      similarMovieIds: [858, 1213, 318, 296]
    },
    {
      movieId: 296,
      title: "Pulp Fiction (1994)",
      cleanTitle: "Pulp Fiction",
      year: 1994,
      genres: ["Comedy", "Crime", "Drama", "Thriller"],
      primaryGenre: "Crime",
      ratingAvg: 4.19,
      ratingCount: 78735,
      duration: "154 phút",
      director: "Quentin Tarantino",
      cast: ["John Travolta", "Uma Thurman", "Samuel L. Jackson"],
      writer: "Quentin Tarantino, Roger Avary",
      posterUrl: "https://image.tmdb.org/t/p/w500/vQWk5YBFWF4bZaofAbv0tShwBvQ.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/suaEOtk1N1sgg2MTM7oZd2cfVp3.jpg",
      links: {
        imdbId: "0110912",
        tmdbId: "680",
        imdbUrl: "https://www.imdb.com/title/tt0110912/",
        tmdbUrl: "https://www.themoviedb.org/movie/680"
      },
      synopsis: "Những câu chuyện đan xen bất tận trong thế giới ngầm Los Angeles của hai tay sát thủ yêu triết lý, một tay đấm bốc và vợ của trùm xã hội đen.",
      similarMovieIds: [50, 2959, 1213, 858]
    },
    {
      movieId: 356,
      title: "Forrest Gump (1994)",
      cleanTitle: "Forrest Gump",
      year: 1994,
      genres: ["Comedy", "Drama", "Romance", "War"],
      primaryGenre: "Drama",
      ratingAvg: 4.05,
      ratingCount: 80375,
      duration: "142 phút",
      director: "Robert Zemeckis",
      cast: ["Tom Hanks", "Robin Wright", "Gary Sinise"],
      writer: "Winston Groom, Eric Roth",
      posterUrl: "https://image.tmdb.org/t/p/w500/saHP97rTPS5eLmrLQEcANmKrsFl.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/66Kn4XWhkuPkJxOJyPEx4U2CUfN.jpg",
      links: {
        imdbId: "0109830",
        tmdbId: "13",
        imdbUrl: "https://www.imdb.com/title/tt0109830/",
        tmdbUrl: "https://www.themoviedb.org/movie/13"
      },
      synopsis: "Cuộc đời kỳ diệu của người đàn ông giản dị với chỉ số IQ 75 nhưng đã vô tình chứng kiến và tác động đến các sự kiện lịch sử vĩ đại nhất của nước Mỹ thế kỷ 20.",
      similarMovieIds: [318, 527, 1, 260]
    },
    {
      movieId: 593,
      title: "The Silence of the Lambs (1991)",
      cleanTitle: "The Silence of the Lambs",
      year: 1991,
      genres: ["Crime", "Horror", "Thriller"],
      primaryGenre: "Thriller",
      ratingAvg: 4.15,
      ratingCount: 73109,
      duration: "118 phút",
      director: "Jonathan Demme",
      cast: ["Jodie Foster", "Anthony Hopkins", "Scott Glenn"],
      writer: "Thomas Harris, Ted Tally",
      posterUrl: "https://image.tmdb.org/t/p/w500/uS9m8OBk1A8eM9I042bx8XXpqAq.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/mbOx1wxMLikzwWUO9TKAcFIy6op.jpg",
      links: {
        imdbId: "0102926",
        tmdbId: "274",
        imdbUrl: "https://www.imdb.com/title/tt0102926/",
        tmdbUrl: "https://www.themoviedb.org/movie/274"
      },
      synopsis: "Học viên FBI trẻ Clarice Starling phải tìm kiếm sự cố vấn từ kẻ ăn thịt người Hannibal Lecter đang bị giam cầm để truy bắt một kẻ giết người hàng loạt khác.",
      similarMovieIds: [50, 47, 296, 1219]
    },
    {
      movieId: 2571,
      title: "The Matrix (1999)",
      cleanTitle: "The Matrix",
      year: 1999,
      genres: ["Action", "Sci-Fi", "Thriller"],
      primaryGenre: "Sci-Fi",
      ratingAvg: 4.15,
      ratingCount: 71787,
      duration: "136 phút",
      director: "The Wachowskis",
      cast: ["Keanu Reeves", "Laurence Fishburne", "Carrie-Anne Moss"],
      writer: "Lana Wachowski, Lilly Wachowski",
      posterUrl: "https://image.tmdb.org/t/p/w500/dXNAPwY7VrqMAo51EKhhCJfaGb5.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/tlm8UkiQsitc8rSuIAscQDCnP8d.jpg",
      links: {
        imdbId: "0133093",
        tmdbId: "603",
        imdbUrl: "https://www.imdb.com/title/tt0133093/",
        tmdbUrl: "https://www.themoviedb.org/movie/603"
      },
      synopsis: "Một lập trình viên kiêm hacker bí danh Neo phát hiện ra thực tại mà nhân loại đang sống chỉ là một chương trình mô phỏng do máy móc thống trị tạo ra.",
      similarMovieIds: [79132, 109487, 589, 1214]
    },
    {
      movieId: 260,
      title: "Star Wars: Episode IV - A New Hope (1977)",
      cleanTitle: "Star Wars: Episode IV - A New Hope",
      year: 1977,
      genres: ["Action", "Adventure", "Sci-Fi"],
      primaryGenre: "Adventure",
      ratingAvg: 4.12,
      ratingCount: 68083,
      duration: "121 phút",
      director: "George Lucas",
      cast: ["Mark Hamill", "Harrison Ford", "Carrie Fisher"],
      writer: "George Lucas",
      posterUrl: "https://image.tmdb.org/t/p/w500/fai0rspsNeJCS69wHNjOdWxcI7P.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/zqkmTXzjkAgXmEWLRsY4UpTWCeo.jpg",
      links: {
        imdbId: "0076759",
        tmdbId: "11",
        imdbUrl: "https://www.imdb.com/title/tt0076759/",
        tmdbUrl: "https://www.themoviedb.org/movie/11"
      },
      synopsis: "Chàng trai trẻ Luke Skywalker bước vào cuộc chiến không gian cùng các hiệp sĩ Jedi và phe Nổi dậy nhằm lật đổ Đế chế Thiên hà tàn bạo.",
      similarMovieIds: [1196, 2571, 109487, 480]
    },
    {
      movieId: 480,
      title: "Jurassic Park (1993)",
      cleanTitle: "Jurassic Park",
      year: 1993,
      genres: ["Action", "Adventure", "Sci-Fi", "Thriller"],
      primaryGenre: "Adventure",
      ratingAvg: 3.68,
      ratingCount: 63268,
      duration: "127 phút",
      director: "Steven Spielberg",
      cast: ["Sam Neill", "Laura Dern", "Jeff Goldblum"],
      writer: "Michael Crichton, David Koepp",
      posterUrl: "https://image.tmdb.org/t/p/w500/d9mtMGQDLANKieb9PbD3yK7xxzo.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/f082quUW2kAtZXFZVGEfhwacZoG.jpg",
      links: {
        imdbId: "0107290",
        tmdbId: "329",
        imdbUrl: "https://www.imdb.com/title/tt0107290/",
        tmdbUrl: "https://www.themoviedb.org/movie/329"
      },
      synopsis: "Một công viên khủng long nhân bản vô tính trên đảo hoang bị sụp đổ hệ thống an ninh, đẩy nhóm nhà khoa học vào cuộc chiến sinh tồn đẫm máu.",
      similarMovieIds: [589, 260, 356, 110]
    },
    {
      movieId: 527,
      title: "Schindler's List (1993)",
      cleanTitle: "Schindler's List",
      year: 1993,
      genres: ["Drama", "War"],
      primaryGenre: "Drama",
      ratingAvg: 4.25,
      ratingCount: 59349,
      duration: "195 phút",
      director: "Steven Spielberg",
      cast: ["Liam Neeson", "Ben Kingsley", "Ralph Fiennes"],
      writer: "Thomas Keneally, Steven Zaillian",
      posterUrl: "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/zb6fM1CX41D9rF9hdgclu0peUmy.jpg",
      links: {
        imdbId: "0108052",
        tmdbId: "424",
        imdbUrl: "https://www.imdb.com/title/tt0108052/",
        tmdbUrl: "https://www.themoviedb.org/movie/424"
      },
      synopsis: "Câu chuyện có thật về doanh nhân người Đức Oskar Schindler đã dũng cảm cứu sống hơn một nghìn người Do Thái khỏi nạn diệt chủng Holocaust.",
      similarMovieIds: [318, 1208, 1193, 858]
    },
    {
      movieId: 110,
      title: "Braveheart (1995)",
      cleanTitle: "Braveheart",
      year: 1995,
      genres: ["Action", "Drama", "War"],
      primaryGenre: "Action",
      ratingAvg: 4.03,
      ratingCount: 58266,
      duration: "178 phút",
      director: "Mel Gibson",
      cast: ["Mel Gibson", "Sophie Marceau", "Patrick McGoohan"],
      writer: "Randall Wallace",
      posterUrl: "https://image.tmdb.org/t/p/w500/or1gBugydmjToAEq7OZY0owwFk.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/1m1c5gIWWkb1FEC9lzsoXHhhs7b.jpg",
      links: {
        imdbId: "0112573",
        tmdbId: "197",
        imdbUrl: "https://www.imdb.com/title/tt0112573/",
        tmdbUrl: "https://www.themoviedb.org/movie/197"
      },
      synopsis: "Người anh hùng William Wallace lãnh đạo nhân dân Scotland nổi dậy chống lại sự cai trị áp bức của vua Edward I nước Anh trong thế kỷ 13.",
      similarMovieIds: [589, 480, 2028, 356]
    },
    {
      movieId: 589,
      title: "Terminator 2: Judgment Day (1991)",
      cleanTitle: "Terminator 2: Judgment Day",
      year: 1991,
      genres: ["Action", "Sci-Fi"],
      primaryGenre: "Action",
      ratingAvg: 3.96,
      ratingCount: 57379,
      duration: "137 phút",
      director: "James Cameron",
      cast: ["Arnold Schwarzenegger", "Linda Hamilton", "Edward Furlong"],
      writer: "James Cameron, William Wisher",
      posterUrl: "https://image.tmdb.org/t/p/w500/jFTVD4XoWQTcg7wdyJKa8PEds5q.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/izkMjmhauFx9DjoBQqM5sM5WAwE.jpg",
      links: {
        imdbId: "0103064",
        tmdbId: "280",
        imdbUrl: "https://www.imdb.com/title/tt0103064/",
        tmdbUrl: "https://www.themoviedb.org/movie/280"
      },
      synopsis: "Một người máy hủy diệt phiên bản cũ được tái lập trình và gửi về quá khứ để bảo vệ cậu bé John Connor khỏi kẻ săn lùng kim loại lỏng tối tân T-1000.",
      similarMovieIds: [2571, 480, 260, 110]
    },
    {
      movieId: 50,
      title: "The Usual Suspects (1995)",
      cleanTitle: "The Usual Suspects",
      year: 1995,
      genres: ["Crime", "Mystery", "Thriller"],
      primaryGenre: "Mystery",
      ratingAvg: 4.28,
      ratingCount: 55102,
      duration: "106 phút",
      director: "Bryan Singer",
      cast: ["Kevin Spacey", "Gabriel Byrne", "Chazz Palminteri"],
      writer: "Christopher McQuarrie",
      posterUrl: "https://image.tmdb.org/t/p/w500/99X2SgyFunJFXGAYnDv3sb9pnUD.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/hy0Hx9fMPk2fmw26Li60z1S2giU.jpg",
      links: {
        imdbId: "0114814",
        tmdbId: "629",
        imdbUrl: "https://www.imdb.com/title/tt0114814/",
        tmdbUrl: "https://www.themoviedb.org/movie/629"
      },
      synopsis: "Một kẻ tàn tật sống sót sau vụ nổ tàu đẫm máu kể lại câu chuyện quanh 5 tên tội phạm và sự hiện diện ma quái của ông trùm vô hình Keyser Soze.",
      similarMovieIds: [296, 318, 858, 47]
    },
    {
      movieId: 1193,
      title: "One Flew Over the Cuckoo's Nest (1975)",
      cleanTitle: "One Flew Over the Cuckoo's Nest",
      year: 1975,
      genres: ["Drama"],
      primaryGenre: "Drama",
      ratingAvg: 4.24,
      ratingCount: 42105,
      duration: "133 phút",
      director: "Milos Forman",
      cast: ["Jack Nicholson", "Louise Fletcher", "Will Sampson"],
      writer: "Lawrence Hauben, Bo Goldman",
      posterUrl: "https://image.tmdb.org/t/p/w500/kjWsMh72V6d8KRLV4EOoSJLT1H7.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/uA8eSNAUUUyfHNIrG4h0zHxzt9W.jpg",
      links: {
        imdbId: "0073486",
        tmdbId: "510",
        imdbUrl: "https://www.imdb.com/title/tt0073486/",
        tmdbUrl: "https://www.themoviedb.org/movie/510"
      },
      synopsis: "Một tên tội phạm bất cần giả điên để trốn lao động khổ sai đã khơi dậy tinh thần phản kháng cho các bệnh nhân trong một trại tâm thần độc tài.",
      similarMovieIds: [318, 527, 858, 1208]
    },
    {
      movieId: 912,
      title: "Casablanca (1942)",
      cleanTitle: "Casablanca",
      year: 1942,
      genres: ["Drama", "Romance"],
      primaryGenre: "Romance",
      ratingAvg: 4.22,
      ratingCount: 31250,
      duration: "102 phút",
      director: "Michael Curtiz",
      cast: ["Humphrey Bogart", "Ingrid Bergman", "Paul Henreid"],
      writer: "Julius J. Epstein, Philip G. Epstein",
      posterUrl: "https://image.tmdb.org/t/p/w500/lGCEKlJo2CnWydQj7aamY7s1S7Q.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/87wqeMeUeMRLjsE1IWNKJcPlpuC.jpg",
      links: {
        imdbId: "0034583",
        tmdbId: "289",
        imdbUrl: "https://www.imdb.com/title/tt0034583/",
        tmdbUrl: "https://www.themoviedb.org/movie/289"
      },
      synopsis: "Tại thành phố cảng Casablanca thời Thế chiến II, một chủ quán bar người Mỹ hoài nghi gặp lại người tình cũ và đứng trước lựa chọn hy sinh tình yêu vì đại nghĩa.",
      similarMovieIds: [904, 858, 1212, 1208]
    },
    {
      movieId: 904,
      title: "Rear Window (1954)",
      cleanTitle: "Rear Window",
      year: 1954,
      genres: ["Mystery", "Thriller"],
      primaryGenre: "Mystery",
      ratingAvg: 4.23,
      ratingCount: 22108,
      duration: "112 phút",
      director: "Alfred Hitchcock",
      cast: ["James Stewart", "Grace Kelly", "Wendell Corey"],
      writer: "John Michael Hayes, Cornell Woolrich",
      posterUrl: "https://image.tmdb.org/t/p/w500/ILVF0eJxHMddjxeQhswFtpMtqx.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/5bN06p5OwRUEqcfrtNs5egV16yb.jpg",
      links: {
        imdbId: "0047396",
        tmdbId: "567",
        imdbUrl: "https://www.imdb.com/title/tt0047396/",
        tmdbUrl: "https://www.themoviedb.org/movie/567"
      },
      synopsis: "Một nhiếp ảnh gia bị gãy chân phải ngồi xe lăn giết thời gian bằng cách nhìn trộm hàng xóm qua cửa sổ và dần tin rằng mình đã chứng kiến một vụ giết người.",
      similarMovieIds: [1219, 912, 50, 1212]
    },
    {
      movieId: 1208,
      title: "Apocalypse Now (1979)",
      cleanTitle: "Apocalypse Now",
      year: 1979,
      genres: ["Action", "Drama", "War"],
      primaryGenre: "War",
      ratingAvg: 4.13,
      ratingCount: 28410,
      duration: "147 phút",
      director: "Francis Ford Coppola",
      cast: ["Marlon Brando", "Martin Sheen", "Robert Duvall"],
      writer: "John Milius, Francis Ford Coppola",
      posterUrl: "https://image.tmdb.org/t/p/w500/gQB8Y5RCMkv2zwzFHbUJX3kAhvA.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/49fzLedFVKgGgFChLMuulDJBY1c.jpg",
      links: {
        imdbId: "0078788",
        tmdbId: "28",
        imdbUrl: "https://www.imdb.com/title/tt0078788/",
        tmdbUrl: "https://www.themoviedb.org/movie/28"
      },
      synopsis: "Chuyến hải trình ngược dòng sông vào sâu trong rừng rậm của Đại úy Willard nhằm thi hành nhiệm vụ ám sát bí mật Đại tá Walter Kurtz đã phát điên.",
      similarMovieIds: [858, 527, 1217, 1233]
    },
    {
      movieId: 1213,
      title: "Goodfellas (1990)",
      cleanTitle: "Goodfellas",
      year: 1990,
      genres: ["Crime", "Drama"],
      primaryGenre: "Crime",
      ratingAvg: 4.21,
      ratingCount: 45620,
      duration: "145 phút",
      director: "Martin Scorsese",
      cast: ["Robert De Niro", "Ray Liotta", "Joe Pesci"],
      writer: "Nicholas Pileggi, Martin Scorsese",
      posterUrl: "https://image.tmdb.org/t/p/w500/9OkCLM73MIU2CrKZbqiT8Ln1wY2.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/gILte6Zd7m1YneIr6MVhh30S9pr.jpg",
      links: {
        imdbId: "0099685",
        tmdbId: "769",
        imdbUrl: "https://www.imdb.com/title/tt0099685/",
        tmdbUrl: "https://www.themoviedb.org/movie/769"
      },
      synopsis: "Câu chuyện chân thực về sự thăng trầm kéo dài ba thập kỷ của Henry Hill trong giới giang hồ mafia New York từ khi còn là một cậu bé giao báo.",
      similarMovieIds: [858, 1221, 296, 50]
    },
    {
      movieId: 79132,
      title: "Inception (2010)",
      cleanTitle: "Inception",
      year: 2010,
      genres: ["Action", "Crime", "Drama", "Mystery", "Sci-Fi", "Thriller"],
      primaryGenre: "Sci-Fi",
      ratingAvg: 4.16,
      ratingCount: 65120,
      duration: "148 phút",
      director: "Christopher Nolan",
      cast: ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Elliot Page"],
      writer: "Christopher Nolan",
      posterUrl: "https://image.tmdb.org/t/p/w500/xlaY2zyzMfkhk0HSC5VUwzoZPU1.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/8ZTVqvKDQ8emSGUEMjsS4yHAwrp.jpg",
      links: {
        imdbId: "1375666",
        tmdbId: "27205",
        imdbUrl: "https://www.imdb.com/title/tt1375666/",
        tmdbUrl: "https://www.themoviedb.org/movie/27205"
      },
      synopsis: "Một tên trộm bậc thầy chuyên đánh cắp bí mật từ tiềm thức của người khác trong giấc mơ nhận nhiệm vụ ngược lại: cấy một ý niệm vào tâm trí người thừa kế tập đoàn.",
      similarMovieIds: [2571, 109487, 2959, 48780]
    },
    {
      movieId: 109487,
      title: "Interstellar (2014)",
      cleanTitle: "Interstellar",
      year: 2014,
      genres: ["Adventure", "Drama", "Sci-Fi"],
      primaryGenre: "Sci-Fi",
      ratingAvg: 4.10,
      ratingCount: 54100,
      duration: "169 phút",
      director: "Christopher Nolan",
      cast: ["Matthew McConaughey", "Anne Hathaway", "Jessica Chastain"],
      writer: "Jonathan Nolan, Christopher Nolan",
      posterUrl: "https://image.tmdb.org/t/p/w500/yQvGrMoipbRoddT0ZR8tPoR7NfX.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/8sNiAPPYU14PUepFNeSNGUTiHW.jpg",
      links: {
        imdbId: "0816692",
        tmdbId: "157336",
        imdbUrl: "https://www.imdb.com/title/tt0816692/",
        tmdbUrl: "https://www.themoviedb.org/movie/157336"
      },
      synopsis: "Khi Trái Đất đối mặt với thảm họa tuyệt chủng, một nhóm nhà thám hiểm vũ trụ vượt qua lỗ sâu để tìm kiếm ngôi nhà mới cho nhân loại giữa các vì sao.",
      similarMovieIds: [79132, 2571, 260, 1196]
    },
    {
      movieId: 2959,
      title: "Fight Club (1999)",
      cleanTitle: "Fight Club",
      year: 1999,
      genres: ["Action", "Crime", "Drama", "Thriller"],
      primaryGenre: "Drama",
      ratingAvg: 4.23,
      ratingCount: 68150,
      duration: "139 phút",
      director: "David Fincher",
      cast: ["Brad Pitt", "Edward Norton", "Helena Bonham Carter"],
      writer: "Chuck Palahniuk, Jim Uhls",
      posterUrl: "https://image.tmdb.org/t/p/w500/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/c6OLXfKAk5BKeR6broC8pYiCquX.jpg",
      links: {
        imdbId: "0137523",
        tmdbId: "550",
        imdbUrl: "https://www.imdb.com/title/tt0137523/",
        tmdbUrl: "https://www.themoviedb.org/movie/550"
      },
      synopsis: "Một nhân viên văn phòng mất ngủ kết thân với tay bán xà phòng kỳ quặc Tyler Durden và lập nên sàn đấu ngầm giải tỏa ức chế xã hội tiêu dùng.",
      similarMovieIds: [296, 47, 79132, 50]
    },
    {
      movieId: 47,
      title: "Se7en (1995)",
      cleanTitle: "Se7en",
      year: 1995,
      genres: ["Crime", "Mystery", "Thriller"],
      primaryGenre: "Mystery",
      ratingAvg: 4.14,
      ratingCount: 52180,
      duration: "127 phút",
      director: "David Fincher",
      cast: ["Brad Pitt", "Morgan Freeman", "Gwyneth Paltrow"],
      writer: "Andrew Kevin Walker",
      posterUrl: "https://image.tmdb.org/t/p/w500/191nKfP0ehp3uIvWqgPbFmI4lv9.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/i5H7zusQGsysGQ8i6P361Vnr0n2.jpg",
      links: {
        imdbId: "0114369",
        tmdbId: "807",
        imdbUrl: "https://www.imdb.com/title/tt0114369/",
        tmdbUrl: "https://www.themoviedb.org/movie/807"
      },
      synopsis: "Hai thám tử cảnh sát truy lùng một kẻ giết người hàng loạt tàn bạo sử dụng bảy mối tội đầu trong kinh thánh làm động cơ cho các vụ án mạng.",
      similarMovieIds: [50, 593, 2959, 1219]
    },
    {
      movieId: 1219,
      title: "Psycho (1960)",
      cleanTitle: "Psycho",
      year: 1960,
      genres: ["Crime", "Horror", "Mystery", "Thriller"],
      primaryGenre: "Horror",
      ratingAvg: 4.15,
      ratingCount: 31400,
      duration: "109 phút",
      director: "Alfred Hitchcock",
      cast: ["Anthony Perkins", "Janet Leigh", "Vera Miles"],
      writer: "Robert Bloch, Joseph Stefano",
      posterUrl: "https://image.tmdb.org/t/p/w500/yz4QVqPx3h1hD1DfqqQkCq3rmxW.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/mufF1aYvwdpKerhq5R1YrVcbJLY.jpg",
      links: {
        imdbId: "0054215",
        tmdbId: "539",
        imdbUrl: "https://www.imdb.com/title/tt0054215/",
        tmdbUrl: "https://www.themoviedb.org/movie/539"
      },
      synopsis: "Một nữ thư ký biển thủ tiền chạy trốn và dừng chân tại một nhà nghỉ hẻo lánh do chàng trai trẻ Norman Bates kỳ quặc và người mẹ bí ẩn cai quản.",
      similarMovieIds: [904, 593, 1258, 47]
    },
    {
      movieId: 1258,
      title: "The Shining (1980)",
      cleanTitle: "The Shining",
      year: 1980,
      genres: ["Horror"],
      primaryGenre: "Horror",
      ratingAvg: 4.12,
      ratingCount: 38450,
      duration: "146 phút",
      director: "Stanley Kubrick",
      cast: ["Jack Nicholson", "Shelley Duvall", "Danny Lloyd"],
      writer: "Stephen King, Stanley Kubrick, Diane Johnson",
      posterUrl: "https://image.tmdb.org/t/p/w500/uAR0AWqhQL1hQa69UDEbb2rE5Wx.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/AdKA2F1SzYPhSZdEbjH1Zh75UVQ.jpg",
      links: {
        imdbId: "0081505",
        tmdbId: "694",
        imdbUrl: "https://www.imdb.com/title/tt0081505/",
        tmdbUrl: "https://www.themoviedb.org/movie/694"
      },
      synopsis: "Một nhà văn nhận việc trông coi khách sạn Overlook biệt lập vào mùa đông tuyết trắng và dần phát điên bởi những thế lực siêu nhiên hắc ám.",
      similarMovieIds: [1219, 593, 1348, 1208]
    },
    {
      movieId: 1348,
      title: "Nosferatu (1922)",
      cleanTitle: "Nosferatu",
      year: 1922,
      genres: ["Horror"],
      primaryGenre: "Horror",
      ratingAvg: 3.92,
      ratingCount: 9240,
      duration: "94 phút",
      director: "F.W. Murnau",
      cast: ["Max Schreck", "Gustav von Wangenheim", "Greta Schröder"],
      writer: "Henrik Galeen, Bram Stoker",
      posterUrl: "https://image.tmdb.org/t/p/w500/zv7J85D8CC9qYagAEhPM63CIG6j.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/cA9iGtvjRGJHzDBfrq48l0eyCvA.jpg",
      links: {
        imdbId: "0013442",
        tmdbId: "653",
        imdbUrl: "https://www.imdb.com/title/tt0013442/",
        tmdbUrl: "https://www.themoviedb.org/movie/653"
      },
      synopsis: "Kiệt tác phim câm biểu hiện chủ nghĩa kinh điển về ma cà rồng Bá tước Orlok gieo rắc dịch hạch và sự kinh hoàng khi chuyển đến một thị trấn tại Đức.",
      similarMovieIds: [1219, 1258, 913, 1237]
    },
    {
      movieId: 1,
      title: "Toy Story (1995)",
      cleanTitle: "Toy Story",
      year: 1995,
      genres: ["Adventure", "Animation", "Children", "Comedy", "Fantasy"],
      primaryGenre: "Animation",
      ratingAvg: 3.89,
      ratingCount: 57342,
      duration: "81 phút",
      director: "John Lasseter",
      cast: ["Tom Hanks", "Tim Allen", "Don Rickles"],
      writer: "John Lasseter, Pete Docter, Andrew Stanton",
      posterUrl: "https://image.tmdb.org/t/p/w500/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/8AqWECiUHnz1Crj69uB9vhiK9Le.jpg",
      links: {
        imdbId: "0114709",
        tmdbId: "862",
        imdbUrl: "https://www.imdb.com/title/tt0114709/",
        tmdbUrl: "https://www.themoviedb.org/movie/862"
      },
      synopsis: "Những món đồ chơi biết cử động khi con người vắng mặt. Cuộc phiêu lưu bất đắc dĩ giữa chàng cao bồi Woody và cảnh sát vũ trụ Buzz Lightyear.",
      similarMovieIds: [3114, 6377, 5618, 364]
    },
    {
      movieId: 3114,
      title: "Toy Story 2 (1999)",
      cleanTitle: "Toy Story 2",
      year: 1999,
      genres: ["Adventure", "Animation", "Children", "Comedy", "Fantasy"],
      primaryGenre: "Animation",
      ratingAvg: 3.82,
      ratingCount: 38240,
      duration: "92 phút",
      director: "John Lasseter",
      cast: ["Tom Hanks", "Tim Allen", "Joan Cusack"],
      writer: "John Lasseter, Pete Docter, Ash Brannon",
      posterUrl: "https://image.tmdb.org/t/p/w500/4rbcp3ng8n1MKHjpeqW0L7Fnpzz.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/nsfVr4QbbunUrHINN9N7JdVAMTf.jpg",
      links: {
        imdbId: "0120363",
        tmdbId: "863",
        imdbUrl: "https://www.imdb.com/title/tt0120363/",
        tmdbUrl: "https://www.themoviedb.org/movie/863"
      },
      synopsis: "Woody bị một kẻ buôn bán đồ chơi cuồng đồ cổ đánh cắp, Buzz Lightyear cùng đồng đội lên đường giải cứu bạn trước khi bị bán sang Nhật Bản.",
      similarMovieIds: [1, 6377, 364, 5618]
    },
    {
      movieId: 5618,
      title: "Spirited Away (Sen to Chihiro no kamikakushi) (2001)",
      cleanTitle: "Spirited Away",
      year: 2001,
      genres: ["Adventure", "Animation", "Fantasy"],
      primaryGenre: "Animation",
      ratingAvg: 4.19,
      ratingCount: 32410,
      duration: "125 phút",
      director: "Hayao Miyazaki",
      cast: ["Rumi Hiiragi", "Miyu Irino", "Mari Natsuki"],
      writer: "Hayao Miyazaki",
      posterUrl: "https://image.tmdb.org/t/p/w500/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/m4TUa2ciEWSlk37rOsjiSIvZDXE.jpg",
      links: {
        imdbId: "0245429",
        tmdbId: "129",
        imdbUrl: "https://www.imdb.com/title/tt0245429/",
        tmdbUrl: "https://www.themoviedb.org/movie/129"
      },
      synopsis: "Cô bé 10 tuổi Chihiro lạc vào thế giới linh hồn kỳ ảo do mụ phù thủy Yubaba cai quản và phải nỗ lực làm việc để giải cứu cha mẹ đã bị biến thành heo.",
      similarMovieIds: [1, 364, 6377, 1237]
    },
    {
      movieId: 6377,
      title: "Finding Nemo (2003)",
      cleanTitle: "Finding Nemo",
      year: 2003,
      genres: ["Adventure", "Animation", "Children", "Comedy"],
      primaryGenre: "Children",
      ratingAvg: 3.88,
      ratingCount: 42100,
      duration: "100 phút",
      director: "Andrew Stanton",
      cast: ["Albert Brooks", "Ellen DeGeneres", "Alexander Gould"],
      writer: "Andrew Stanton, Bob Peterson, David Reynolds",
      posterUrl: "https://image.tmdb.org/t/p/w500/eHuGQ10FUzK1mdOY69wF5pGgEf5.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/eCynaAOgYYiw5yN5lBwz3IxqvaW.jpg",
      links: {
        imdbId: "0266543",
        tmdbId: "12",
        imdbUrl: "https://www.imdb.com/title/tt0266543/",
        tmdbUrl: "https://www.themoviedb.org/movie/12"
      },
      synopsis: "Chú cá hề Marlin cùng cô bạn cá Dory đãng trí vượt qua đại dương bao la để tìm kiếm đứa con trai nhỏ Nemo bị thợ lặn bắt đến Sydney.",
      similarMovieIds: [1, 3114, 364, 5618]
    },
    {
      movieId: 364,
      title: "The Lion King (1994)",
      cleanTitle: "The Lion King",
      year: 1994,
      genres: ["Adventure", "Animation", "Children", "Drama", "Musical"],
      primaryGenre: "Children",
      ratingAvg: 3.95,
      ratingCount: 52180,
      duration: "88 phút",
      director: "Roger Allers, Rob Minkoff",
      cast: ["Matthew Broderick", "Jeremy Irons", "James Earl Jones"],
      writer: "Irene Mecchi, Jonathan Roberts, Linda Woolverton",
      posterUrl: "https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/wXsQvli6tWqja51pYxXNG1LFIGV.jpg",
      links: {
        imdbId: "0110357",
        tmdbId: "8587",
        imdbUrl: "https://www.imdb.com/title/tt0110357/",
        tmdbUrl: "https://www.themoviedb.org/movie/8587"
      },
      synopsis: "Sư tử con Simba trốn chạy sau khi vua cha Mufasa bị ám sát bởi người chú xảo quyệt Scar, trước khi quay về đòi lại ngai vàng của Thảo nguyên Kiêu hãnh.",
      similarMovieIds: [1, 899, 6377, 5618]
    },
    {
      movieId: 899,
      title: "Singin' in the Rain (1952)",
      cleanTitle: "Singin' in the Rain",
      year: 1952,
      genres: ["Comedy", "Musical", "Romance"],
      primaryGenre: "Musical",
      ratingAvg: 4.08,
      ratingCount: 18240,
      duration: "103 phút",
      director: "Stanley Donen, Gene Kelly",
      cast: ["Gene Kelly", "Donald O'Connor", "Debbie Reynolds"],
      writer: "Adolph Green, Betty Comden",
      posterUrl: "https://image.tmdb.org/t/p/w500/zjrpWniKbzu0zFR5sUI1Ptdfl9y.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/6qOyw4yfzbzTp5YsCX26C28Do0S.jpg",
      links: {
        imdbId: "0045152",
        tmdbId: "872",
        imdbUrl: "https://www.imdb.com/title/tt0045152/",
        tmdbUrl: "https://www.themoviedb.org/movie/872"
      },
      synopsis: "Một ngôi sao phim câm đối mặt với bước ngoặt chuyển dịch lịch sử của Hollywood sang kỷ nguyên phim có âm thanh cùng sự giúp sức của cô ca sĩ tài năng.",
      similarMovieIds: [364, 912, 1256, 6711]
    },
    {
      movieId: 1256,
      title: "Duck Soup (1933)",
      cleanTitle: "Duck Soup",
      year: 1933,
      genres: ["Comedy", "Musical", "War"],
      primaryGenre: "Comedy",
      ratingAvg: 4.02,
      ratingCount: 12410,
      duration: "68 phút",
      director: "Leo McCarey",
      cast: ["Groucho Marx", "Harpo Marx", "Chico Marx"],
      writer: "Bert Kalmar, Harry Ruby",
      posterUrl: "https://image.tmdb.org/t/p/w500/31t63plEGKHhYuuCpC9bFWO9SBS.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/nVpp3ZcIFtJJ3fJp65eJczehIN8.jpg",
      links: {
        imdbId: "0023969",
        tmdbId: "3063",
        imdbUrl: "https://www.imdb.com/title/tt0023969/",
        tmdbUrl: "https://www.themoviedb.org/movie/3063"
      },
      synopsis: "Kiệt tác hài châm biếm kinh điển của anh em nhà Marx kể về nhà độc tài lập dị Rufus T. Firefly đẩy quốc gia Freedonia vào cuộc chiến tranh nực cười.",
      similarMovieIds: [899, 1217, 3030, 912]
    },
    {
      movieId: 6711,
      title: "Lost in Translation (2003)",
      cleanTitle: "Lost in Translation",
      year: 2003,
      genres: ["Comedy", "Drama", "Romance"],
      primaryGenre: "Romance",
      ratingAvg: 4.03,
      ratingCount: 35120,
      duration: "102 phút",
      director: "Sofia Coppola",
      cast: ["Bill Murray", "Scarlett Johansson", "Giovanni Ribisi"],
      writer: "Sofia Coppola",
      posterUrl: "https://image.tmdb.org/t/p/w500/3jCLmYDIIiSMPujbwygNpqdpM8N.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/6ITVHoipvxAS8luzKtHTbPaHLtT.jpg",
      links: {
        imdbId: "0335266",
        tmdbId: "153",
        imdbUrl: "https://www.imdb.com/title/tt0335266/",
        tmdbUrl: "https://www.themoviedb.org/movie/153"
      },
      synopsis: "Hai tâm hồn cô đơn lạc lõng giữa lòng Tokyo hiện đại tìm thấy sự đồng điệu bất ngờ và tình bạn sâu sắc tại một khách sạn sang trọng.",
      similarMovieIds: [7361, 4144, 307, 3949]
    },
    {
      movieId: 7361,
      title: "Eternal Sunshine of the Spotless Mind (2004)",
      cleanTitle: "Eternal Sunshine of the Spotless Mind",
      year: 2004,
      genres: ["Drama", "Romance", "Sci-Fi"],
      primaryGenre: "Romance",
      ratingAvg: 4.10,
      ratingCount: 42105,
      duration: "108 phút",
      director: "Michel Gondry",
      cast: ["Jim Carrey", "Kate Winslet", "Kirsten Dunst"],
      writer: "Charlie Kaufman, Michel Gondry",
      posterUrl: "https://image.tmdb.org/t/p/w500/5MwkWH9tYHv3mV9OdYTMR5qreIz.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/95qi5TJMIBI5VzWHia88Pbrye7Z.jpg",
      links: {
        imdbId: "0338013",
        tmdbId: "38",
        imdbUrl: "https://www.imdb.com/title/tt0338013/",
        tmdbUrl: "https://www.themoviedb.org/movie/38"
      },
      synopsis: "Một cặp đôi trải qua thủ tục y tế xóa sạch ký ức về nhau sau khi chia tay, chỉ để nhận ra tình yêu đích thực không dễ dàng bị lãng quên.",
      similarMovieIds: [6711, 4144, 3949, 307]
    },
    {
      movieId: 3949,
      title: "Requiem for a Dream (2000)",
      cleanTitle: "Requiem for a Dream",
      year: 2000,
      genres: ["Drama"],
      primaryGenre: "Drama",
      ratingAvg: 4.09,
      ratingCount: 31200,
      duration: "102 phút",
      director: "Darren Aronofsky",
      cast: ["Ellen Burstyn", "Jared Leto", "Jennifer Connelly"],
      writer: "Hubert Selby Jr., Darren Aronofsky",
      posterUrl: "https://image.tmdb.org/t/p/w500/9BTwsLaMVHOGFlmsSlx5QYCaXb.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/fAGYRJCujRBMw7TCuTp893eSG8e.jpg",
      links: {
        imdbId: "0180093",
        tmdbId: "641",
        imdbUrl: "https://www.imdb.com/title/tt0180093/",
        tmdbUrl: "https://www.themoviedb.org/movie/641"
      },
      synopsis: "Bức tranh ám ảnh và tàn khốc về sự suy sụp thể xác lẫn tâm hồn của bốn con người tại Brooklyn bị giam cầm trong những cơn nghiện thuốc và ảo vọng.",
      similarMovieIds: [6711, 307, 1237, 4144]
    },
    {
      movieId: 307,
      title: "Three Colors: Blue (Trois couleurs: Bleu) (1993)",
      cleanTitle: "Three Colors: Blue",
      year: 1993,
      genres: ["Drama"],
      primaryGenre: "Drama",
      ratingAvg: 4.18,
      ratingCount: 14200,
      duration: "98 phút",
      director: "Krzysztof Kieslowski",
      cast: ["Juliette Binoche", "Zbigniew Zamachowski", "Julie Delpy"],
      writer: "Krzysztof Kieslowski, Krzysztof Piesiewicz",
      posterUrl: "https://image.tmdb.org/t/p/w500/33wsWxzsNstI8N7dvuwzFmj1qBd.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/pXvYw0QOPbHJVvwGbZfrSNY2vnB.jpg",
      links: {
        imdbId: "0108394",
        tmdbId: "108",
        imdbUrl: "https://www.imdb.com/title/tt0108394/",
        tmdbUrl: "https://www.themoviedb.org/movie/108"
      },
      synopsis: "Một phụ nữ đấu tranh tìm lại sự tự do tinh thần và vượt qua nỗi đau đớn tột cùng sau cái chết bất ngờ của chồng và con gái trong tai nạn xe hơi.",
      similarMovieIds: [1237, 4144, 3949, 6711]
    },
    {
      movieId: 1237,
      title: "The Seventh Seal (Sjunde inseglet) (1957)",
      cleanTitle: "The Seventh Seal",
      year: 1957,
      genres: ["Drama"],
      primaryGenre: "Drama",
      ratingAvg: 4.17,
      ratingCount: 18450,
      duration: "96 phút",
      director: "Ingmar Bergman",
      cast: ["Max von Sydow", "Gunnar Björnstrand", "Bengt Ekerot"],
      writer: "Ingmar Bergman",
      posterUrl: "https://image.tmdb.org/t/p/w500/dGgiXMWDcS5aJTBEFu7bmaQPNox.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/vxEfLEdPbUJW8ZD9ymGQ6ZJzuyf.jpg",
      links: {
        imdbId: "0050976",
        tmdbId: "11645",
        imdbUrl: "https://www.imdb.com/title/tt0050976/",
        tmdbUrl: "https://www.themoviedb.org/movie/11645"
      },
      synopsis: "Hiệp sĩ thời Trung cổ Antonius Block trở về từ cuộc Thập tự chinh và thách đấu một ván cờ sinh tử với Thần Chết giữa dịch bệnh Cái Chết Đen hoành hành.",
      similarMovieIds: [307, 4144, 1208, 1217]
    },
    {
      movieId: 4144,
      title: "In the Mood for Love (Fa yeung nin wa) (2000)",
      cleanTitle: "In the Mood for Love",
      year: 2000,
      genres: ["Drama", "Romance"],
      primaryGenre: "Romance",
      ratingAvg: 4.19,
      ratingCount: 19800,
      duration: "98 phút",
      director: "Vương Gia Vệ (Wong Kar-wai)",
      cast: ["Lương Triều Vỹ", "Trương Mạn Ngọc", "Phan Địch Hoa"],
      writer: "Vương Gia Vệ (Wong Kar-wai)",
      posterUrl: "https://image.tmdb.org/t/p/w500/8BgGbbWiLNhPtkMkN0gGTnbtvBv.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/ffQFnAUm2Uu4RU0nijpjPRf9TBT.jpg",
      links: {
        imdbId: "0235940",
        tmdbId: "843",
        imdbUrl: "https://www.imdb.com/title/tt0235940/",
        tmdbUrl: "https://www.themoviedb.org/movie/843"
      },
      synopsis: "Tại Hồng Kông thập niên 1960, hai người hàng xóm phát hiện vợ và chồng của họ ngoại tình với nhau, dần hình thành một tình cảm câm lặng và day dứt.",
      similarMovieIds: [6711, 7361, 307, 1237]
    },
    {
      movieId: 6016,
      title: "City of God (Cidade de Deus) (2002)",
      cleanTitle: "City of God",
      year: 2002,
      genres: ["Action", "Adventure", "Crime", "Drama", "Thriller"],
      primaryGenre: "Crime",
      ratingAvg: 4.28,
      ratingCount: 29800,
      duration: "130 phút",
      director: "Fernando Meirelles",
      cast: ["Alexandre Rodrigues", "Leandro Firmino", "Phellipe Haagensen"],
      writer: "Paulo Lins, Bráulio Mantovani",
      posterUrl: "https://image.tmdb.org/t/p/w500/k7eYdWvhYQyRQoU2TB2A2Xu2TfD.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/uvitbjFU4JqvMwIkMWHp69bmUzG.jpg",
      links: {
        imdbId: "0317248",
        tmdbId: "598",
        imdbUrl: "https://www.imdb.com/title/tt0317248/",
        tmdbUrl: "https://www.themoviedb.org/movie/598"
      },
      synopsis: "Bức tranh khốc liệt về sự trưởng thành của hai cậu bé tại khu ổ chuột Rio de Janeiro: một người trở thành nhiếp ảnh gia, người kia thành trùm ma túy.",
      similarMovieIds: [318, 858, 296, 1213]
    },
    {
      movieId: 1217,
      title: "Ran (1985)",
      cleanTitle: "Ran",
      year: 1985,
      genres: ["Action", "Drama", "War"],
      primaryGenre: "Drama",
      ratingAvg: 4.23,
      ratingCount: 15410,
      duration: "162 phút",
      director: "Akira Kurosawa",
      cast: ["Tatsuya Nakadai", "Akira Terao", "Jinpachi Nezu"],
      writer: "Akira Kurosawa, Hideo Oguni, Masato Ide",
      posterUrl: "https://image.tmdb.org/t/p/w500/dGgiXMWDcS5aJTBEFu7bmaQPNox.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/vxEfLEdPbUJW8ZD9ymGQ6ZJzuyf.jpg",
      links: {
        imdbId: "0089881",
        tmdbId: "11645",
        imdbUrl: "https://www.imdb.com/title/tt0089881/",
        tmdbUrl: "https://www.themoviedb.org/movie/11645"
      },
      synopsis: "Chuyển thể sử thi bi kịch Vua Lear vào bối cảnh Nhật Bản thời Chiến Quốc: lãnh chúa Hidetora chia lâu đài cho 3 con trai dẫn đến chiến tranh huynh đệ tương tàn.",
      similarMovieIds: [1208, 3030, 1178, 2019]
    },
    {
      movieId: 1233,
      title: "The Boat (Das Boot) (1981)",
      cleanTitle: "The Boat (Das Boot)",
      year: 1981,
      genres: ["Action", "Drama", "War"],
      primaryGenre: "War",
      ratingAvg: 4.19,
      ratingCount: 18200,
      duration: "149 phút",
      director: "Wolfgang Petersen",
      cast: ["Jürgen Prochnow", "Herbert Grönemeyer", "Klaus Wennemann"],
      writer: "Lothar G. Buchheim, Wolfgang Petersen",
      posterUrl: "https://image.tmdb.org/t/p/w500/hNfAYNCMRthp9iruF5Q6S1z4bVA.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/zzzhbZnSPMOON9uGt0LsdUJWYoC.jpg",
      links: {
        imdbId: "0082096",
        tmdbId: "387",
        imdbUrl: "https://www.imdb.com/title/tt0082096/",
        tmdbUrl: "https://www.themoviedb.org/movie/387"
      },
      synopsis: "Áp lực tâm lý nghẹt thở và sự khắc nghiệt tột cùng của thủy thủ đoàn tàu ngầm Đức U-96 tuần tra trên biển Đại Tây Dương trong Thế chiến II.",
      similarMovieIds: [1208, 1217, 1178, 527]
    },
    {
      movieId: 3030,
      title: "Yojimbo (1961)",
      cleanTitle: "Yojimbo",
      year: 1961,
      genres: ["Action", "Drama"],
      primaryGenre: "Action",
      ratingAvg: 4.18,
      ratingCount: 14100,
      duration: "110 phút",
      director: "Akira Kurosawa",
      cast: ["Toshirô Mifune", "Tatsuya Nakadai", "Yôko Tsukasa"],
      writer: "Ryûzô Kikushima, Akira Kurosawa",
      posterUrl: "https://image.tmdb.org/t/p/w500/tN7kYPjRhDolpui9sc9Eq9n5b2O.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/5BBwSVytssbFuSPZE4DtJVhROjN.jpg",
      links: {
        imdbId: "0055630",
        tmdbId: "11878",
        imdbUrl: "https://www.imdb.com/title/tt0055630/",
        tmdbUrl: "https://www.themoviedb.org/movie/11878"
      },
      synopsis: "Một võ sĩ samurai vô chủ thông minh đến một thị trấn nhỏ bị chia rẽ bởi hai băng đảng tội phạm và dùng mưu kế khiến chúng tự tiêu diệt lẫn nhau.",
      similarMovieIds: [1217, 1201, 2019, 1266]
    },
    {
      movieId: 1178,
      title: "Paths of Glory (1957)",
      cleanTitle: "Paths of Glory",
      year: 1957,
      genres: ["Drama", "War"],
      primaryGenre: "War",
      ratingAvg: 4.21,
      ratingCount: 16200,
      duration: "88 phút",
      director: "Stanley Kubrick",
      cast: ["Kirk Douglas", "Ralph Meeker", "Adolphe Menjou"],
      writer: "Stanley Kubrick, Calder Willingham, Jim Thompson",
      posterUrl: "https://image.tmdb.org/t/p/w500/hOrV2fCw2kmSiS4ZMGFPfXqr3lt.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/1pRNzOM7OQA29cVayaCheBI4vn7.jpg",
      links: {
        imdbId: "0050825",
        tmdbId: "102",
        imdbUrl: "https://www.imdb.com/title/tt0050825/",
        tmdbUrl: "https://www.themoviedb.org/movie/102"
      },
      synopsis: "Đại tá Dax phải biện hộ tại tòa án binh cho ba người lính vô tội bị các tướng lĩnh cấp cao chọn làm vật tế thần sau một cuộc tấn công tự sát bất thành.",
      similarMovieIds: [1208, 1217, 1233, 527]
    },
    {
      movieId: 1212,
      title: "The Third Man (1949)",
      cleanTitle: "The Third Man",
      year: 1949,
      genres: ["Film-Noir", "Mystery", "Thriller"],
      primaryGenre: "Film-Noir",
      ratingAvg: 4.19,
      ratingCount: 17200,
      duration: "104 phút",
      director: "Carol Reed",
      cast: ["Joseph Cotten", "Alida Valli", "Orson Welles"],
      writer: "Graham Greene",
      posterUrl: "https://image.tmdb.org/t/p/w500/7oaie3ZBc9UuWZLF24crro1pone.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/nJ0jz1J3zNja31UEMeklhgFeMw5.jpg",
      links: {
        imdbId: "0041959",
        tmdbId: "1090",
        imdbUrl: "https://www.imdb.com/title/tt0041959/",
        tmdbUrl: "https://www.themoviedb.org/movie/1090"
      },
      synopsis: "Một nhà văn người Mỹ đến Vienna thời hậu chiến và bị cuốn vào cuộc điều tra về cái chết bí ẩn của người bạn thân Harry Lime giữa thế giới ngầm.",
      similarMovieIds: [913, 904, 912, 1219]
    },
    {
      movieId: 913,
      title: "The Maltese Falcon (1941)",
      cleanTitle: "The Maltese Falcon",
      year: 1941,
      genres: ["Film-Noir", "Mystery"],
      primaryGenre: "Film-Noir",
      ratingAvg: 4.16,
      ratingCount: 21400,
      duration: "100 phút",
      director: "John Huston",
      cast: ["Humphrey Bogart", "Mary Astor", "Gladys George"],
      writer: "Dashiell Hammett, John Huston",
      posterUrl: "https://image.tmdb.org/t/p/w500/bf4o6Uzw5wqLjdKwRuiDrN1xyvl.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/5lMm0MmAviP6DF45nxBVOT9LCwK.jpg",
      links: {
        imdbId: "0033870",
        tmdbId: "963",
        imdbUrl: "https://www.imdb.com/title/tt0033870/",
        tmdbUrl: "https://www.themoviedb.org/movie/963"
      },
      synopsis: "Thám tử tư Sam Spade nhận vụ án tìm kiếm bức tượng chim ưng Malta nạm đá quý vô giá và bị vây quanh bởi những kẻ lừa đảo nguy hiểm.",
      similarMovieIds: [1212, 904, 912, 50]
    },
    {
      movieId: 1201,
      title: "The Good, the Bad and the Ugly (1966)",
      cleanTitle: "The Good, the Bad and the Ugly",
      year: 1966,
      genres: ["Action", "Adventure", "Western"],
      primaryGenre: "Western",
      ratingAvg: 4.21,
      ratingCount: 35120,
      duration: "178 phút",
      director: "Sergio Leone",
      cast: ["Clint Eastwood", "Eli Wallach", "Lee Van Cleef"],
      writer: "Luciano Vincenzoni, Sergio Leone",
      posterUrl: "https://image.tmdb.org/t/p/w500/bX2xnavhMYjWDoZp1VM6VnU1xwe.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/x4biAVdPVCghBlsVIzB6NmbghIz.jpg",
      links: {
        imdbId: "0060196",
        tmdbId: "429",
        imdbUrl: "https://www.imdb.com/title/tt0060196/",
        tmdbUrl: "https://www.themoviedb.org/movie/429"
      },
      synopsis: "Ba tay súng bất hảo trong thời kỳ Nội chiến Mỹ hợp tác và lừa gạt lẫn nhau trong cuộc đua tìm kiếm kho báu vàng của quân đội chôn tại nghĩa địa.",
      similarMovieIds: [1266, 3030, 110, 589]
    },
    {
      movieId: 1266,
      title: "Unforgiven (1992)",
      cleanTitle: "Unforgiven",
      year: 1992,
      genres: ["Drama", "Western"],
      primaryGenre: "Western",
      ratingAvg: 4.11,
      ratingCount: 28400,
      duration: "131 phút",
      director: "Clint Eastwood",
      cast: ["Clint Eastwood", "Gene Hackman", "Morgan Freeman"],
      writer: "David Webb Peoples",
      posterUrl: "https://image.tmdb.org/t/p/w500/54roTwbX9fltg85zjsmrooXAs12.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/rvRGFevvZK48onX0PYI1eQLbuJd.jpg",
      links: {
        imdbId: "0105695",
        tmdbId: "33",
        imdbUrl: "https://www.imdb.com/title/tt0105695/",
        tmdbUrl: "https://www.themoviedb.org/movie/33"
      },
      synopsis: "Một cựu sát thủ già đã gác súng chấp nhận một phi vụ săn tiền thưởng cuối cùng cùng người bạn cũ và một chàng trai trẻ.",
      similarMovieIds: [1201, 3030, 858, 318]
    },
    {
      movieId: 96606,
      title: "Samsara (2011)",
      cleanTitle: "Samsara",
      year: 2011,
      genres: ["Documentary"],
      primaryGenre: "Documentary",
      ratingAvg: 4.14,
      ratingCount: 8450,
      duration: "102 phút",
      director: "Ron Fricke",
      cast: ["Balinese dancers", "Tibetan monks", "Indigenous peoples"],
      writer: "Ron Fricke, Mark Magidson",
      posterUrl: "https://image.tmdb.org/t/p/w500/qodkea4k0pNUmNTl5TJO2PdTqgW.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/tbSjemOf1nXPOjWELdaeZ7qj1iX.jpg",
      links: {
        imdbId: "0770802",
        tmdbId: "89708",
        imdbUrl: "https://www.imdb.com/title/tt0770802/",
        tmdbUrl: "https://www.themoviedb.org/movie/89708"
      },
      synopsis: "Bộ phim tài liệu hình ảnh không lời thoại kỳ vĩ quay bằng phim 70mm tại 25 quốc gia, khám phá vòng luân hồi sinh tử và bản chất kỳ diệu của nhân loại.",
      similarMovieIds: [8644, 1237, 307, 4144]
    },
    {
      movieId: 8644,
      title: "Fahrenheit 9/11 (2004)",
      cleanTitle: "Fahrenheit 9/11",
      year: 2004,
      genres: ["Documentary"],
      primaryGenre: "Documentary",
      ratingAvg: 3.75,
      ratingCount: 16400,
      duration: "122 phút",
      director: "Michael Moore",
      cast: ["Michael Moore", "George W. Bush", "Ben Affleck"],
      writer: "Michael Moore",
      posterUrl: "https://image.tmdb.org/t/p/w500/9Fha6OFqFBL9bPRLJPhJFmAwib6.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/mW7HEM3e6Uf9IcBuvEHS8yaQ48M.jpg",
      links: {
        imdbId: "0361596",
        tmdbId: "1777",
        imdbUrl: "https://www.imdb.com/title/tt0361596/",
        tmdbUrl: "https://www.themoviedb.org/movie/1777"
      },
      synopsis: "Bộ phim tài liệu chính trị đoạt giải Cành cọ Vàng khảo sát nước Mỹ sau sự kiện 11/9 và các mối quan hệ dẫn đến cuộc chiến tranh Iraq.",
      similarMovieIds: [96606, 1208, 1178, 527]
    },
    {
      movieId: 7153,
      title: "The Lord of the Rings: The Return of the King (2003)",
      cleanTitle: "The Lord of the Rings: The Return of the King",
      year: 2003,
      genres: ["Action", "Adventure", "Drama", "Fantasy"],
      primaryGenre: "Fantasy",
      ratingAvg: 4.26,
      ratingCount: 61400,
      duration: "201 phút",
      director: "Peter Jackson",
      cast: ["Elijah Wood", "Viggo Mortensen", "Ian McKellen"],
      writer: "J.R.R. Tolkien, Fran Walsh, Peter Jackson",
      posterUrl: "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/ctiw6FZK4N36LmkjSklWEbuvlq9.jpg",
      links: {
        imdbId: "0167260",
        tmdbId: "122",
        imdbUrl: "https://www.imdb.com/title/tt0167260/",
        tmdbUrl: "https://www.themoviedb.org/movie/122"
      },
      synopsis: "Trận chiến quyết định vận mệnh Trung Địa tại Minas Tirith khi Frodo và Sam tiến gần đến Núi Doom để hủy diệt Chiếc Nhẫn Quyền Lực duy nhất.",
      similarMovieIds: [4993, 260, 1196, 3578]
    },
    {
      movieId: 4993,
      title: "The Lord of the Rings: The Fellowship of the Ring (2001)",
      cleanTitle: "The Lord of the Rings: The Fellowship of the Ring",
      year: 2001,
      genres: ["Adventure", "Fantasy"],
      primaryGenre: "Fantasy",
      ratingAvg: 4.20,
      ratingCount: 65400,
      duration: "178 phút",
      director: "Peter Jackson",
      cast: ["Elijah Wood", "Ian McKellen", "Orlando Bloom"],
      writer: "J.R.R. Tolkien, Fran Walsh, Peter Jackson",
      posterUrl: "https://image.tmdb.org/t/p/w500/6oom5QYQ2yQTMJIbnvbkBL9cHo6.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/oiwc338EoBgS4sEI2ixAny4KQKg.jpg",
      links: {
        imdbId: "0120737",
        tmdbId: "120",
        imdbUrl: "https://www.imdb.com/title/tt0120737/",
        tmdbUrl: "https://www.themoviedb.org/movie/120"
      },
      synopsis: "Chàng Hobbit Frodo Baggins thừa kế chiếc nhẫn quyền năng và cùng Hiệp hội Nhẫn gồm 9 thành viên bắt đầu chuyến hành trình nguy hiểm tới Mordor.",
      similarMovieIds: [7153, 260, 1196, 2571]
    },
    {
      movieId: 205425,
      title: "Araya (1959)",
      cleanTitle: "Araya",
      year: 1959,
      genres: ["(no genres listed)"],
      primaryGenre: "(no genres listed)",
      ratingAvg: 3.85,
      ratingCount: 420,
      duration: "82 phút",
      director: "Margot Benacerraf",
      cast: ["José Ignacio Cabrujas", "Laurent Terzieff"],
      writer: "Margot Benacerraf, Pierre Seghers",
      posterUrl: "https://image.tmdb.org/t/p/w500/dt3kIO57I0y58YPKh2JAXxZfXGw.jpg",
      backdropUrl: "https://image.tmdb.org/t/p/w1280/qbA4t0x8Cdvkd0L3VT3868SvqNv.jpg",
      links: {
        imdbId: "0052573",
        tmdbId: "77678",
        imdbUrl: "https://www.imdb.com/title/tt0052573/",
        tmdbUrl: "https://www.themoviedb.org/movie/77678"
      },
      synopsis: "Tác phẩm điện ảnh thơ đoạt giải FIPRESCI tại LHP Cannes miêu tả cuộc sống lao động khắc khổ kéo dài hàng thế kỷ của những diêm dân trên bán đảo muối Araya hoang vu.",
      similarMovieIds: [96606, 1237, 307, 1212]
    }
  ];

  // =========================================================================
  // 2.1 BỔ SUNG METADATA TIẾNG VIỆT, TÂM TRẠNG & TỌA ĐỘ 3D CHO 53 PHIM
  // =========================================================================
  const MOVIE_ENRICHMENT_MAP = {
    318: {
      vietnameseTitle: "Nhà Tù Shawshank",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Hy vọng", "Kiên cường", "Tự do", "Tình bạn"],
      tasteFeatures: { depth: 0.95, pacing: 0.45, auteur: 0.88, tone: 0.70 },
      embedding3d: { x: 28.5, y: 45.2, z: -15.4, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Đồng thuận tuyệt đối Top 1 giữa mô hình ALS và Knowledge Graph."
    },
    111: {
      vietnameseTitle: "Tài Xế Taxi",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Cô độc", "Ám ảnh", "Bạo lực ngầm", "Đô thị đêm"],
      tasteFeatures: { depth: 0.92, pacing: 0.38, auteur: 0.98, tone: 0.15 },
      embedding3d: { x: -45.2, y: 12.8, z: 62.1, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Trùng khớp đạo diễn Martin Scorsese và phong cách Auteur gai góc."
    },
    858: {
      vietnameseTitle: "Bố Già",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Quyền lực", "Gia tộc", "Bi kịch", "Kinh điển"],
      tasteFeatures: { depth: 0.98, pacing: 0.50, auteur: 0.96, tone: 0.25 },
      embedding3d: { x: -38.4, y: 32.1, z: 48.7, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Kiệt tác tội phạm gia tộc đạt điểm phân vị cao nhất trong cụm người xem cùng gu."
    },
    1221: {
      vietnameseTitle: "Bố Già Phần II",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Sụp đổ", "Tha hóa", "Sử thi gia tộc", "Đỉnh cao"],
      tasteFeatures: { depth: 0.99, pacing: 0.48, auteur: 0.97, tone: 0.20 },
      embedding3d: { x: -41.2, y: 35.0, z: 52.3, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Sử thi tội phạm tiếp nối Bố Già, đạt điểm số tuyệt đối từ mạng lưới Genome."
    },
    296: {
      vietnameseTitle: "Chuyện Tào Lao",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Phi tuyến tính", "Hài đen", "Hội thoại sắc sảo", "Đột phá"],
      tasteFeatures: { depth: 0.85, pacing: 0.80, auteur: 0.99, tone: 0.55 },
      embedding3d: { x: 55.4, y: -22.1, z: 35.8, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Đích kiểm chuẩn Held-out Validation của bạn với điểm 5.0★."
    },
    356: {
      vietnameseTitle: "Cuộc Đời Forrest Gump",
      primaryMood: "uplifting",
      moodLabel: "Thư giãn / Vui tươi sảng khoái",
      moodTags: ["Ấm áp", "Cảm động", "Lạc quan", "Lịch sử"],
      tasteFeatures: { depth: 0.82, pacing: 0.65, auteur: 0.75, tone: 0.90 },
      embedding3d: { x: 18.2, y: 62.4, z: -35.1, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Cảm xúc ấm áp, lạc quan, tương thích cao với phân khúc phim đại chúng xuất sắc."
    },
    593: {
      vietnameseTitle: "Sự Im Lặng Của Bầy Cừu",
      primaryMood: "suspense",
      moodLabel: "Hồi hộp / Ly kỳ thót tim",
      moodTags: ["Tâm lý tội phạm", "Nghẹt thở", "Đấu trí", "Rùng rợn"],
      tasteFeatures: { depth: 0.90, pacing: 0.75, auteur: 0.88, tone: 0.18 },
      embedding3d: { x: -62.3, y: -15.2, z: 22.4, clusterId: "cluster_thriller", clusterName: "Cụm Hồi Hộp & Giật Gân" },
      provenanceSummary: "Đấu trí tâm lý tội phạm đỉnh cao giữa Hannibal Lecter và Clarice Starling."
    },
    2571: {
      vietnameseTitle: "Ma Trận",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Triết học nhận thức", "Hành động cách mạng", "Kỷ nguyên số", "Kinh điển Sci-Fi"],
      tasteFeatures: { depth: 0.91, pacing: 0.88, auteur: 0.92, tone: 0.40 },
      embedding3d: { x: 72.1, y: -38.5, z: -55.2, clusterId: "cluster_scifi", clusterName: "Cụm Khoa Học Viễn Tưởng & Kỳ Ảo" },
      provenanceSummary: "Mốc son triết học nhận thức kết hợp kỹ xảo Bullet-time cách mạng."
    },
    260: {
      vietnameseTitle: "Chiến Tranh Giữa Các Vì Sao IV",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Sử thi vũ trụ", "Anh hùng thần thoại", "Choáng ngợp", "Kỷ niệm tuổi thơ"],
      tasteFeatures: { depth: 0.75, pacing: 0.82, auteur: 0.85, tone: 0.75 },
      embedding3d: { x: 65.4, y: -25.0, z: -68.3, clusterId: "cluster_scifi", clusterName: "Cụm Khoa Học Viễn Tưởng & Kỳ Ảo" },
      provenanceSummary: "Khởi nguyên sử thi không gian huyền thoại của đạo diễn George Lucas."
    },
    480: {
      vietnameseTitle: "Công Viên Kỷ Jura",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Khủng long", "Kỳ quan kỹ xảo", "Hồi hộp", "Bom tấn kinh điển"],
      tasteFeatures: { depth: 0.70, pacing: 0.85, auteur: 0.82, tone: 0.60 },
      embedding3d: { x: 42.1, y: -12.4, z: -45.0, clusterId: "cluster_adventure", clusterName: "Cụm Phiêu Lưu & Khám Phá" },
      provenanceSummary: "Kỳ quan kỹ xảo tái sinh loài khủng long của Steven Spielberg."
    },
    527: {
      vietnameseTitle: "Bản Danh Sách Của Schindler",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Diệt chủng", "Nhân tính", "Cảm động sâu sắc", "Trắng đen bất hủ"],
      tasteFeatures: { depth: 0.99, pacing: 0.40, auteur: 0.95, tone: 0.12 },
      embedding3d: { x: 12.5, y: 75.0, z: -10.2, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Bi ca xúc động về lòng nhân ái cứu vớt hơn 1,100 sinh mạng thời Thế chiến."
    },
    110: {
      vietnameseTitle: "Trái Tim Quả Cảm",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Tự do", "Chiến trận sử thi", "Ý chí quật cường", "Hào hùng"],
      tasteFeatures: { depth: 0.85, pacing: 0.78, auteur: 0.86, tone: 0.45 },
      embedding3d: { x: 35.8, y: 15.2, z: -58.4, clusterId: "cluster_adventure", clusterName: "Cụm Phiêu Lưu & Khám Phá" },
      provenanceSummary: "Bản hùng ca bất hủ về khát vọng tự do của người anh hùng William Wallace."
    },
    589: {
      vietnameseTitle: "Kẻ Hủy Diệt 2: Ngày Phán Xét",
      primaryMood: "suspense",
      moodLabel: "Hồi hộp / Ly kỳ thót tim",
      moodTags: ["Hành động nghẹt thở", "Trí tuệ nhân tạo", "Tình mẫu tử", "Mốc son kỹ xảo"],
      tasteFeatures: { depth: 0.80, pacing: 0.92, auteur: 0.85, tone: 0.40 },
      embedding3d: { x: 15.6, y: -45.0, z: -35.2, clusterId: "cluster_thriller", clusterName: "Cụm Hồi Hộp & Giật Gân" },
      provenanceSummary: "Đỉnh cao phim hành động khoa học viễn tưởng với hiệu ứng kim loại lỏng T-1000."
    },
    50: {
      vietnameseTitle: "Nghi Phạm Vô Tội",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Cú lừa ngoạn mục", "Keyser Söze", "Hỏi cung tâm lý", "Bậc thầy kịch bản"],
      tasteFeatures: { depth: 0.92, pacing: 0.70, auteur: 0.90, tone: 0.35 },
      embedding3d: { x: 48.2, y: -18.5, z: 28.6, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Mê cung thẩm vấn và cú lừa danh tính ngoạn mục bậc nhất lịch sử điện ảnh."
    },
    1193: {
      vietnameseTitle: "Bay Trên Tổ Chim Cúc Cu",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Khát vọng tự do", "Phản kháng áp bức", "Diễn xuất đỉnh cao", "Chua xót"],
      tasteFeatures: { depth: 0.96, pacing: 0.52, auteur: 0.95, tone: 0.50 },
      embedding3d: { x: 22.0, y: 68.1, z: 5.4, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Khúc tráng ca phản kháng của Jack Nicholson đoạt trọn vẹn 5 giải Oscar lớn."
    },
    912: {
      vietnameseTitle: "Chuyện Tình Casablanca",
      primaryMood: "romantic",
      moodLabel: "Lãng mạn / Day dứt ngọt ngào",
      moodTags: ["Tình yêu hy sinh", "Chiến tranh hoài niệm", "Hội thoại bất hủ", "Quý phái"],
      tasteFeatures: { depth: 0.90, pacing: 0.55, auteur: 0.92, tone: 0.65 },
      embedding3d: { x: -15.4, y: 42.0, z: -72.0, clusterId: "cluster_romance", clusterName: "Cụm Lãng Mạn & Cảm Xúc" },
      provenanceSummary: "Tượng đài lãng mạn thời chiến với giai điệu As Time Goes By bất tử."
    },
    904: {
      vietnameseTitle: "Khung Cửa Sổ Phía Sau",
      primaryMood: "suspense",
      moodLabel: "Hồi hộp / Ly kỳ thót tim",
      moodTags: ["Nhìn lén tò mò", "Án mạng chung cư", "Bậc thầy Hitchcock", "Căng thẳng tinh tế"],
      tasteFeatures: { depth: 0.88, pacing: 0.68, auteur: 0.98, tone: 0.55 },
      embedding3d: { x: -55.0, y: -8.0, z: 18.0, clusterId: "cluster_thriller", clusterName: "Cụm Hồi Hộp & Giật Gân" },
      provenanceSummary: "Nghệ thuật căng thẳng đỉnh cao qua góc nhìn ống kính viễn vọng của Hitchcock."
    },
    1208: {
      vietnameseTitle: "Ngày Tận Thế",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Điên loạn chiến tranh", "Tâm lý ảo giác", "Kiệt tác hình ảnh", "Trầm luân"],
      tasteFeatures: { depth: 0.99, pacing: 0.35, auteur: 0.99, tone: 0.08 },
      embedding3d: { x: -68.0, y: 20.0, z: 55.0, clusterId: "cluster_war", clusterName: "Cụm Chiến Tranh & Lịch Sử" },
      provenanceSummary: "Hành trình ngược dòng sông vào cõi điên loạn tột cùng của chiến tranh."
    },
    1213: {
      vietnameseTitle: "Siêu Trộm Thân Thiết",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Thế giới ngầm Mafia", "Nhịp phim cuồng nhiệt", "Chân thực gai góc", "Scorsese"],
      tasteFeatures: { depth: 0.90, pacing: 0.85, auteur: 0.95, tone: 0.30 },
      embedding3d: { x: -35.0, y: 25.0, z: 42.0, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Chân dung thế giới ngầm New York qua lăng kính siêu tốc của Martin Scorsese."
    },
    79132: {
      vietnameseTitle: "Kẻ Cắp Giấc Mơ",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Tầng lớp giấc mơ", "Đánh cắp ý niệm", "Nolan đỉnh cao", "Nghịch lý thời gian"],
      tasteFeatures: { depth: 0.94, pacing: 0.86, auteur: 0.94, tone: 0.50 },
      embedding3d: { x: 68.0, y: -30.0, z: -40.0, clusterId: "cluster_scifi", clusterName: "Cụm Khoa Học Viễn Tưởng & Kỳ Ảo" },
      provenanceSummary: "Kiến trúc giấc mơ đa tầng đầy trí tuệ với âm nhạc dội bom của Hans Zimmer."
    },
    109487: {
      vietnameseTitle: "Hố Đen Tử Thần",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Lỗ sâu không gian", "Tình cha con vượt thời gian", "Vật lý thiên văn", "Tráng lệ"],
      tasteFeatures: { depth: 0.93, pacing: 0.72, auteur: 0.94, tone: 0.65 },
      embedding3d: { x: 75.0, y: -15.0, z: -62.0, clusterId: "cluster_scifi", clusterName: "Cụm Khoa Học Viễn Tưởng & Kỳ Ảo" },
      provenanceSummary: "Tình phụ tử vượt qua không gian 5 chiều và hố đen Gargantua vĩ đại."
    },
    2959: {
      vietnameseTitle: "Sàn Đấu Sinh Tử",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Đa nhân cách", "Phản văn hóa tiêu dùng", "Bạo lực giải phóng", "Fincher"],
      tasteFeatures: { depth: 0.95, pacing: 0.82, auteur: 0.96, tone: 0.22 },
      embedding3d: { x: 58.0, y: -10.0, z: 40.0, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Cú đấm trực diện vào chủ nghĩa tiêu dùng qua nhân vật ảo tưởng Tyler Durden."
    },
    47: {
      vietnameseTitle: "Bảy Tội Lỗi Chết Người",
      primaryMood: "suspense",
      moodLabel: "Hồi hộp / Ly kỳ thót tim",
      moodTags: ["Sát nhân liên hoàn", "7 mối tội đầu", "Mưa u uất New York", "Kết cục chấn động"],
      tasteFeatures: { depth: 0.92, pacing: 0.74, auteur: 0.95, tone: 0.10 },
      embedding3d: { x: -58.0, y: -20.0, z: 30.0, clusterId: "cluster_thriller", clusterName: "Cụm Hồi Hộp & Giật Gân" },
      provenanceSummary: "Án mạng liên hoàn kinh hoàng theo 7 mối tội đầu và cái kết hộp quà gây sốc."
    },
    1219: {
      vietnameseTitle: "Tâm Thần Hoảng Loạn",
      primaryMood: "suspense",
      moodLabel: "Hồi hộp / Ly kỳ thót tim",
      moodTags: ["Cảnh phòng tắm kinh điển", "Tâm thần phân liệt", "Âm nhạc rợn gáy", "Hitchcock"],
      tasteFeatures: { depth: 0.88, pacing: 0.70, auteur: 0.98, tone: 0.15 },
      embedding3d: { x: -65.0, y: -28.0, z: 12.0, clusterId: "cluster_thriller", clusterName: "Cụm Hồi Hộp & Giật Gân" },
      provenanceSummary: "Phát súng định hình thể loại tâm lý rùng rợn hiện đại của Alfred Hitchcock."
    },
    1258: {
      vietnameseTitle: "Ngôi Nhà Ma Ám",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Khách sạn Overlook", "Điên loạn cách ly", "Kubrick đối xứng", "Ám ảnh kinh hoàng"],
      tasteFeatures: { depth: 0.94, pacing: 0.42, auteur: 0.99, tone: 0.12 },
      embedding3d: { x: -52.0, y: 15.0, z: 45.0, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Không gian đối xứng lạnh gáy và màn hóa điên ám ảnh của Jack Torrance."
    },
    1348: {
      vietnameseTitle: "Ma Cà Rồng Nosferatu",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Biểu hiện Đức", "Bóng đen gothic", "Phim câm tiên phong", "Huyền thoại ma cà rồng"],
      tasteFeatures: { depth: 0.90, pacing: 0.30, auteur: 0.98, tone: 0.10 },
      embedding3d: { x: -60.0, y: 8.0, z: 50.0, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Kiệt tác trường phái Biểu hiện Đức mở đầu kỷ nguyên ma cà rồng điện ảnh."
    },
    1: {
      vietnameseTitle: "Câu Chuyện Đồ Chơi",
      primaryMood: "uplifting",
      moodLabel: "Thư giãn / Vui tươi sảng khoái",
      moodTags: ["Tuổi thơ đồ chơi", "Tình bạn Woody & Buzz", "Cách mạng 3D Pixar", "Ấm áp"],
      tasteFeatures: { depth: 0.75, pacing: 0.78, auteur: 0.85, tone: 0.95 },
      embedding3d: { x: -25.0, y: -45.0, z: -85.0, clusterId: "cluster_animation", clusterName: "Cụm Hoạt Hình & Gia Đình" },
      provenanceSummary: "Tác phẩm hoạt hình 3D dài đầu tiên trong lịch sử nhân loại, chan chứa tình bạn."
    },
    3114: {
      vietnameseTitle: "Câu Chuyện Đồ Chơi 2",
      primaryMood: "uplifting",
      moodLabel: "Thư giãn / Vui tươi sảng khoái",
      moodTags: ["Sưu tập đồ cổ", "Giá trị tình bạn", "Hài hước cảm động", "Pixar"],
      tasteFeatures: { depth: 0.76, pacing: 0.79, auteur: 0.84, tone: 0.92 },
      embedding3d: { x: -22.0, y: -42.0, z: -82.0, clusterId: "cluster_animation", clusterName: "Cụm Hoạt Hình & Gia Đình" },
      provenanceSummary: "Sự tiếp nối hoàn hảo về ý nghĩa của việc trưởng thành và giá trị ký ức tuổi thơ."
    },
    5618: {
      vietnameseTitle: "Vùng Đất Linh Hồn",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Thế giới thần linh", "Trưởng thành dũng cảm", "Miyazaki kỳ diệu", "Oscar hoạt hình"],
      tasteFeatures: { depth: 0.95, pacing: 0.60, auteur: 0.99, tone: 0.80 },
      embedding3d: { x: -10.0, y: -30.0, z: -75.0, clusterId: "cluster_animation", clusterName: "Cụm Hoạt Hình & Gia Đình" },
      provenanceSummary: "Tuyệt tác hoạt hình Studio Ghibli đoạt giải Oscar với trí tưởng tượng bay bổng."
    },
    6377: {
      vietnameseTitle: "Đi Tìm Nemo",
      primaryMood: "uplifting",
      moodLabel: "Thư giãn / Vui tươi sảng khoái",
      moodTags: ["Đại dương rực rỡ", "Tình phụ tử bao la", "Hài hước vui nhộn", "Vượt khó"],
      tasteFeatures: { depth: 0.72, pacing: 0.75, auteur: 0.80, tone: 0.92 },
      embedding3d: { x: -30.0, y: -50.0, z: -78.0, clusterId: "cluster_animation", clusterName: "Cụm Hoạt Hình & Gia Đình" },
      provenanceSummary: "Hành trình vượt rạn san hô vĩ đại minh chứng cho sức mạnh tình phụ tử."
    },
    364: {
      vietnameseTitle: "Vua Sư Tử",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Vòng quay cuộc sống", "Nhạc kịch tráng lệ", "Trưởng thành trách nhiệm", "Disney đỉnh cao"],
      tasteFeatures: { depth: 0.82, pacing: 0.72, auteur: 0.82, tone: 0.85 },
      embedding3d: { x: 10.0, y: -35.0, z: -70.0, clusterId: "cluster_animation", clusterName: "Cụm Hoạt Hình & Gia Đình" },
      provenanceSummary: "Đỉnh cao thời kỳ Phục hưng Disney với giai điệu Circle of Life vang dội."
    },
    899: {
      vietnameseTitle: "Hát Dưới Mưa",
      primaryMood: "uplifting",
      moodLabel: "Thư giãn / Vui tươi sảng khoái",
      moodTags: ["Vũ đạo đỉnh cao", "Kỷ nguyên phim có tiếng", "Yêu đời sảng khoái", "Âm nhạc rực rỡ"],
      tasteFeatures: { depth: 0.70, pacing: 0.80, auteur: 0.90, tone: 0.98 },
      embedding3d: { x: -40.0, y: 10.0, z: -80.0, clusterId: "cluster_romance", clusterName: "Cụm Lãng Mạn & Cảm Xúc" },
      provenanceSummary: "Vũ điệu rực rỡ và nụ cười rạng rỡ của Gene Kelly xóa tan mọi muộn phiền."
    },
    1256: {
      vietnameseTitle: "Canh Vịt Nấu Măng",
      primaryMood: "uplifting",
      moodLabel: "Thư giãn / Vui tươi sảng khoái",
      moodTags: ["Hài hước châm biếm", "Anh em nhà Marx", "Cười nghiêng ngả", "Chính trị hề hước"],
      tasteFeatures: { depth: 0.72, pacing: 0.92, auteur: 0.90, tone: 0.90 },
      embedding3d: { x: 30.0, y: -60.0, z: -10.0, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Hài kịch châm biếm kinh điển đả kích chiến tranh của anh em nhà Marx."
    },
    6711: {
      vietnameseTitle: "Lạc Lối Ở Tokyo",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Cô đơn đô thị", "Đồng điệu tâm hồn", "Tokyo về đêm", "Thì thầm bí mật"],
      tasteFeatures: { depth: 0.92, pacing: 0.32, auteur: 0.95, tone: 0.60 },
      embedding3d: { x: -8.0, y: 55.0, z: -40.0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Bản giao hưởng dịu êm về sự đồng điệu giữa hai tâm hồn lạc lõng giữa Tokyo."
    },
    7361: {
      vietnameseTitle: "Ánh Dương Vĩnh Cửu",
      primaryMood: "romantic",
      moodLabel: "Lãng mạn / Day dứt ngọt ngào",
      moodTags: ["Xóa ký ức tình yêu", "Mê cung tâm trí", "Day dứt ngọt ngào", "Gondry & Kaufman"],
      tasteFeatures: { depth: 0.96, pacing: 0.65, auteur: 0.98, tone: 0.65 },
      embedding3d: { x: -5.0, y: 35.0, z: -65.0, clusterId: "cluster_romance", clusterName: "Cụm Lãng Mạn & Cảm Xúc" },
      provenanceSummary: "Đích kiểm chuẩn Held-out Test của bạn với điểm số tuyệt đối 5.0★."
    },
    3949: {
      vietnameseTitle: "Khát Vọng Cho Một Giấc Mơ",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Cơn nghiện tàn khốc", "Dựng phim hip-hop montage", "Nhạc phim ám ảnh", "Bi kịch tan nát"],
      tasteFeatures: { depth: 0.96, pacing: 0.80, auteur: 0.97, tone: 0.05 },
      embedding3d: { x: 50.0, y: 15.0, z: 65.0, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Hồi chuông cảnh tỉnh bi kịch tan nát của Darren Aronofsky với kỹ thuật montage dồn dập."
    },
    307: {
      vietnameseTitle: "Ba Màu: Xanh Lam",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Nỗi đau mất mát", "Tự do tinh thần", "Kieslowski triết học", "Hình ảnh xanh biếc"],
      tasteFeatures: { depth: 0.98, pacing: 0.25, auteur: 0.99, tone: 0.40 },
      embedding3d: { x: 5.0, y: 80.0, z: -20.0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Triết lý về sự giải phóng cảm xúc sau đau thương của đạo diễn Krzysztof Kieślowski."
    },
    1237: {
      vietnameseTitle: "Phong Ấn Thứ Bảy",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Đánh cờ với Thần Chết", "Dịch hạch Trung cổ", "Ý nghĩa tồn tại", "Bergman"],
      tasteFeatures: { depth: 0.99, pacing: 0.30, auteur: 0.99, tone: 0.30 },
      embedding3d: { x: 62.0, y: 30.0, z: 20.0, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Ván cờ sinh tử với Thần Chết truy tìm ý nghĩa hiện sinh của Ingmar Bergman."
    },
    4144: {
      vietnameseTitle: "Tâm Trạng Khi Yêu",
      primaryMood: "romantic",
      moodLabel: "Lãng mạn / Day dứt ngọt ngào",
      moodTags: ["Vương Gia Vệ", "Sườn xám hoài cổ", "Tình trong như đã mặt ngoài còn e", "Nhạc Waltz du dương"],
      tasteFeatures: { depth: 0.95, pacing: 0.28, auteur: 0.99, tone: 0.60 },
      embedding3d: { x: -18.0, y: 30.0, z: -68.0, clusterId: "cluster_romance", clusterName: "Cụm Lãng Mạn & Cảm Xúc" },
      provenanceSummary: "Chất thơ điện ảnh Á Đông của Vương Gia Vệ trong từng tà áo sườn xám và ánh mắt."
    },
    6016: {
      vietnameseTitle: "Thành Phố Của Chúa",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Khu ổ chuột Rio", "Bạo lực chân thực", "Nhiếp ảnh sinh tồn", "Nhịp phim nghẹt thở"],
      tasteFeatures: { depth: 0.93, pacing: 0.90, auteur: 0.96, tone: 0.18 },
      embedding3d: { x: -30.0, y: 18.0, z: 48.0, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Hiện thực khốc liệt tại khu ổ chuột Cidade de Deus với ống kính máy quay bùng nổ."
    },
    1217: {
      vietnameseTitle: "Loạn",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Vua Lear phiên bản Samurai", "Kurosawa bi tráng", "Màu sắc tương phản", "Tranh đoạt quyền lực"],
      tasteFeatures: { depth: 0.97, pacing: 0.45, auteur: 0.99, tone: 0.20 },
      embedding3d: { x: 18.0, y: 65.0, z: 25.0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Thiên sử thi bi tráng chuyển thể Vua Lear của bậc thầy Akira Kurosawa."
    },
    1233: {
      vietnameseTitle: "Con Tàu U-Boat",
      primaryMood: "suspense",
      moodLabel: "Hồi hộp / Ly kỳ thót tim",
      moodTags: ["Tàu ngầm nghẹt thở", "Áp lực đáy biển", "Chiến tranh hiện thực", "Kinh điển nước Đức"],
      tasteFeatures: { depth: 0.91, pacing: 0.76, auteur: 0.92, tone: 0.25 },
      embedding3d: { x: -62.0, y: 15.0, z: 38.0, clusterId: "cluster_war", clusterName: "Cụm Chiến Tranh & Lịch Sử" },
      provenanceSummary: "Cảm giác ngột ngạt nghẹt thở trong khoang tàu ngầm U-Boat giữa lòng Đại Tây Dương."
    },
    3030: {
      vietnameseTitle: "Võ Sĩ Giác Đấu Yojimbo",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Samurai vô chủ", "Kế ly gián hai phe", "Kurosawa kinh điển", "Tifune Toshiro"],
      tasteFeatures: { depth: 0.88, pacing: 0.72, auteur: 0.98, tone: 0.60 },
      embedding3d: { x: 38.0, y: -15.0, z: 15.0, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Mưu kế ly gián tài tình của kiếm sĩ lang thang định hình cả thể loại Viễn Tây."
    },
    1178: {
      vietnameseTitle: "Hào Quang Danh Vọng",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Chiến tranh hào công", "Sự đê hèn của tướng lĩnh", "Kubrick chống chiến tranh", "Công lý bị chà đạp"],
      tasteFeatures: { depth: 0.98, pacing: 0.60, auteur: 0.98, tone: 0.15 },
      embedding3d: { x: -50.0, y: 35.0, z: 32.0, clusterId: "cluster_war", clusterName: "Cụm Chiến Tranh & Lịch Sử" },
      provenanceSummary: "Vở kịch pháp đình chiến tranh chống phi nghĩa đanh thép của Stanley Kubrick."
    },
    1212: {
      vietnameseTitle: "Người Thứ Ba",
      primaryMood: "dark_noir",
      moodLabel: "U tối / Ám ảnh hiện thực",
      moodTags: ["Vienna sau chiến tranh", "Góc quay nghiêng Dutch angle", "Tiếng đàn zither", "Phim đen đỉnh cao"],
      tasteFeatures: { depth: 0.92, pacing: 0.58, auteur: 0.97, tone: 0.25 },
      embedding3d: { x: -48.0, y: 10.0, z: 58.0, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Hình bóng Harry Lime dưới ánh đèn đường Vienna trong bản giao hưởng Film-Noir mẫu mực."
    },
    913: {
      vietnameseTitle: "Chim Ưng Malta",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Thám tử tư Sam Spade", "Tượng chim ưng huyền bí", "Khởi thủy Film-Noir", "Bogart"],
      tasteFeatures: { depth: 0.89, pacing: 0.68, auteur: 0.94, tone: 0.35 },
      embedding3d: { x: 32.0, y: 5.0, z: 42.0, clusterId: "cluster_crime", clusterName: "Cụm Tội Phạm & Phim Đen" },
      provenanceSummary: "Chất liệu tạo nên những giấc mơ: tác phẩm khởi xướng dòng phim trinh thám gai góc."
    },
    1201: {
      vietnameseTitle: "Tốt, Xấu và Vô Lại",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Miền Tây nước Ý Spaghetti", "Nhạc phim Ennio Morricone", "Màn đọ súng ba góc", "Bất hủ"],
      tasteFeatures: { depth: 0.86, pacing: 0.70, auteur: 0.98, tone: 0.60 },
      embedding3d: { x: 45.0, y: 8.0, z: -50.0, clusterId: "cluster_adventure", clusterName: "Cụm Phiêu Lưu & Khám Phá" },
      provenanceSummary: "Cuộc săn vàng tay ba tại nghĩa địa Sad Hill với âm nhạc Ennio Morricone bất hủ."
    },
    1266: {
      vietnameseTitle: "Không Thể Thứ Tha",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Giải ảo thần thoại Miền Tây", "Sát thủ về già", "Hậu quả bạo lực", "Clint Eastwood"],
      tasteFeatures: { depth: 0.95, pacing: 0.48, auteur: 0.96, tone: 0.22 },
      embedding3d: { x: 25.0, y: 50.0, z: -15.0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Cái nhìn cay đắng về giá máu của bạo lực đoạt 4 giải Oscar của Clint Eastwood."
    },
    96606: {
      vietnameseTitle: "Luân Hồi",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Không lời thoại", "Hình ảnh 70mm kinh ngạc", "Vòng tròn sinh tử", "Trải nghiệm thiền định"],
      tasteFeatures: { depth: 0.99, pacing: 0.20, auteur: 0.99, tone: 0.70 },
      embedding3d: { x: 0.0, y: 85.0, z: 0.0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Bản thiền ca thị giác 70mm đưa tâm trí chu du qua 25 quốc gia không lời thoại."
    },
    8644: {
      vietnameseTitle: "9/11 và Nước Mỹ",
      primaryMood: "mind_bending",
      moodLabel: "Kích thích trí tuệ / Xoắn não",
      moodTags: ["Phóng sự điều tra", "Chiến tranh Iraq", "Chính trị nước Mỹ", "Cành cọ Vàng"],
      tasteFeatures: { depth: 0.88, pacing: 0.75, auteur: 0.92, tone: 0.35 },
      embedding3d: { x: 52.0, y: 22.0, z: 10.0, clusterId: "cluster_auteur", clusterName: "Cụm Phim Đột Phá & Auteur" },
      provenanceSummary: "Góc nhìn tài liệu điều tra đoạt Cành cọ Vàng Cannes gây chấn động dư luận thế giới."
    },
    7153: {
      vietnameseTitle: "Chúa Nhẫn: Sự Trở Về Của Vua",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["11 giải Oscar", "Đại chiến Gondor", "Hủy nhẫn định mệnh", "Đỉnh cao kỳ ảo"],
      tasteFeatures: { depth: 0.92, pacing: 0.82, auteur: 0.96, tone: 0.75 },
      embedding3d: { x: 60.0, y: -20.0, z: -70.0, clusterId: "cluster_scifi", clusterName: "Cụm Khoa Học Viễn Tưởng & Kỳ Ảo" },
      provenanceSummary: "Đại kết cục vinh quang đoạt trọn vẹn 11 giải Oscar của thiên sử thi Chúa Nhẫn."
    },
    4993: {
      vietnameseTitle: "Chúa Nhẫn: Hiệp Hội Nhẫn Thần",
      primaryMood: "epic_adventure",
      moodLabel: "Phiêu lưu kỳ vĩ / Choáng ngợp",
      moodTags: ["Khởi hành từ Shire", "Tình huynh đệ đồng hành", "Kỳ quan Trung Địa", "Sử thi"],
      tasteFeatures: { depth: 0.91, pacing: 0.78, auteur: 0.96, tone: 0.78 },
      embedding3d: { x: 58.0, y: -18.0, z: -68.0, clusterId: "cluster_scifi", clusterName: "Cụm Khoa Học Viễn Tưởng & Kỳ Ảo" },
      provenanceSummary: "Bước chân đầu tiên bước ra khỏi vùng Shire mở ra thế giới Trung Địa kỳ vĩ."
    },
    205425: {
      vietnameseTitle: "Bán Đảo Araya",
      primaryMood: "reflective",
      moodLabel: "Sâu lắng / Chiêm nghiệm",
      moodTags: ["Diêm dân Venezuela", "Chất thơ hiện thực", "Lao động khổ ải", "Cannes phục hồi"],
      tasteFeatures: { depth: 0.95, pacing: 0.22, auteur: 0.98, tone: 0.50 },
      embedding3d: { x: -5.0, y: 70.0, z: 15.0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch & Nhân Văn" },
      provenanceSummary: "Viên ngọc điện ảnh Nam Mỹ phục hồi đạt giải FIPRESCI tại LHP Cannes."
    }
  };

  // Tự động enrich và gắn poster fallback SVG cho toàn bộ Catalog
  CATALOG.forEach(function(movie) {
    const meta = MOVIE_ENRICHMENT_MAP[movie.movieId];
    if (meta) {
      Object.assign(movie, meta);
    } else {
      movie.vietnameseTitle = movie.cleanTitle || movie.title;
      movie.primaryMood = "reflective";
      movie.moodLabel = "Sâu lắng / Chiêm nghiệm";
      movie.moodTags = ["Điện ảnh", "Kinh điển"];
      movie.tasteFeatures = { depth: 0.8, pacing: 0.6, auteur: 0.8, tone: 0.5 };
      movie.embedding3d = { x: 0, y: 0, z: 0, clusterId: "cluster_drama", clusterName: "Cụm Chính Kịch" };
      movie.provenanceSummary = "Tác phẩm chọn lọc kinh điển trong kho tàng MovieLens 25M.";
    }

    const safeTitle = (movie.vietnameseTitle || movie.cleanTitle || "MoodGraph").replace(/"/g, "'");
    const svgData = '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="450" viewBox="0 0 300 450">' +
      '<defs><linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">' +
      '<stop offset="0%" stop-color="#0B0F14"/><stop offset="50%" stop-color="#141A24"/><stop offset="100%" stop-color="#0F141C"/>' +
      '</linearGradient></defs>' +
      '<rect width="300" height="450" fill="url(#bgGrad)"/>' +
      '<rect x="12" y="12" width="276" height="426" fill="none" stroke="rgba(217,119,6,0.35)" stroke-width="1.5" rx="8"/>' +
      '<circle cx="150" cy="180" r="42" fill="none" stroke="rgba(245,158,11,0.25)" stroke-width="1"/>' +
      '<polygon points="144,165 162,180 144,195" fill="#D97706"/>' +
      '<text x="150" y="270" font-family="Georgia, serif" font-size="18" font-weight="600" fill="#F8FAFC" text-anchor="middle">' + safeTitle.slice(0, 22) + '</text>' +
      '<text x="150" y="295" font-family="sans-serif" font-size="12" fill="#94A3B8" text-anchor="middle">' + (safeTitle.length > 22 ? safeTitle.slice(22, 45) : '') + '</text>' +
      '<text x="150" y="340" font-family="monospace" font-size="11" fill="#F59E0B" text-anchor="middle" letter-spacing="2">' + movie.year + '</text>' +
      '<text x="150" y="415" font-family="sans-serif" font-size="10" fill="#64748B" text-anchor="middle">MOODGRAPH EDITORIAL ARCHIVE</text>' +
      '</svg>';
    movie.posterFallbackSvg = 'data:image/svg+xml;utf8,' + encodeURIComponent(svgData);
  });

  // =========================================================================
  // 3. HỒ SƠ NGƯỜI DÙNG USER 1 VÀ CÁC USER KIỂM CHUẨN THỰC NGHIỆM
  // =========================================================================
  const CURRENT_USER = {
    userId: 1,
    name: "Alex Turner (Cinephile)",
    displayName: "Alex Turner (Cinephile)",
    avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&auto=format&fit=crop&q=80",
    bio: "Khán giả đam mê dòng phim tác giả (Auteur Cinema), điện ảnh kinh điển châu Âu và các câu chuyện tâm lý xã hội sâu sắc.",
    ratingsCount: 68,
    meanRating: 3.78,
    activityLevel: "moderate",
    isInAlsTrain: true,
    genreDistribution: {
      "Drama": 51,
      "Comedy": 22,
      "Romance": 17,
      "Adventure": 11,
      "Crime": 7,
      "Fantasy": 5,
      "War": 5,
      "Musical": 5,
      "Sci-Fi": 4,
      "Thriller": 4,
      "Action": 4,
      "Mystery": 4,
      "Children": 3,
      "Animation": 2,
      "Western": 1,
      "Film-Noir": 1,
      "Horror": 1,
      "Documentary": 1
    },
    topFavoriteGenres: ["Drama", "Comedy", "Romance", "Adventure", "Crime"],
    recentRatedMovies: [
      { movieId: 6711, title: "Lost in Translation (2003)", genres: ["Comedy", "Drama", "Romance"], userRating: 5.0, rating: 5.0, timestamp: 1147868622 },
      { movieId: 3949, title: "Requiem for a Dream (2000)", genres: ["Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868678 },
      { movieId: 307, title: "Three Colors: Blue (1993)", genres: ["Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868828 },
      { movieId: 1237, title: "The Seventh Seal (1957)", genres: ["Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868839 },
      { movieId: 4144, title: "In the Mood for Love (2000)", genres: ["Drama", "Romance"], userRating: 5.0, rating: 5.0, timestamp: 1147868898 },
      { movieId: 6016, title: "City of God (2002)", genres: ["Crime", "Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868950 },
      { movieId: 1208, title: "Apocalypse Now (1979)", genres: ["Drama", "War"], userRating: 5.0, rating: 5.0, timestamp: 1147869012 },
      { movieId: 1217, title: "Ran (1985)", genres: ["Action", "Drama", "War"], userRating: 5.0, rating: 5.0, timestamp: 1147869105 },
      { movieId: 1178, title: "Paths of Glory (1957)", genres: ["Drama", "War"], userRating: 5.0, rating: 5.0, timestamp: 1147869150 },
      { movieId: 1212, title: "The Third Man (1949)", genres: ["Film-Noir", "Mystery"], userRating: 5.0, rating: 5.0, timestamp: 1147869200 }
    ],
    get recentRatings() { return this.recentRatedMovies; },
    get genresDistribution() { return this.genreDistribution; },
    heldOutInteractions: {
      validation: {
        movieId: 296,
        title: "Pulp Fiction (1994)",
        rating: 5.0,
        purpose: "Validation Target (Held-out)"
      },
      test: {
        movieId: 7361,
        title: "Eternal Sunshine of the Spotless Mind (2004)",
        rating: 5.0,
        purpose: "Test Target (Held-out)"
      }
    }
  };

  const PRESET_PERSONAS = {
    user1: {
      id: "user1",
      userId: 1,
      name: "Alex Turner",
      displayName: "Alex Turner (Cinephile)",
      roleDescription: "Hình sự / Tâm lý kinh điển",
      avatarLetter: "A",
      avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&auto=format&fit=crop&q=80",
      bio: "Khán giả đam mê dòng phim tác giả (Auteur Cinema), điện ảnh kinh điển châu Âu và các câu chuyện tâm lý xã hội sâu sắc.",
      ratingsCount: 68,
      meanRating: 3.78,
      activityLevel: "moderate",
      isInAlsTrain: true,
      defaultSliders: { depth: 0.85, pacing: 0.50, auteur: 0.85, tone: 0.35 },
      initialRatings: { 318: 5.0, 858: 5.0, 1208: 4.5, 6016: 5.0, 1212: 5.0, 3949: 5.0 },
      genreDistribution: {
        "Drama": 51, "Comedy": 22, "Romance": 17, "Adventure": 11, "Crime": 7,
        "Fantasy": 5, "War": 5, "Musical": 5, "Sci-Fi": 4, "Thriller": 4, "Action": 4, "Film-Noir": 3
      },
      topFavoriteGenres: ["Drama", "Crime", "Mystery", "War", "Film-Noir"],
      recentRatedMovies: [
        { movieId: 6711, title: "Lost in Translation (2003)", genres: ["Comedy", "Drama", "Romance"], userRating: 5.0, rating: 5.0, timestamp: 1147868622 },
        { movieId: 3949, title: "Requiem for a Dream (2000)", genres: ["Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868678 },
        { movieId: 307, title: "Three Colors: Blue (1993)", genres: ["Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868828 },
        { movieId: 1237, title: "The Seventh Seal (1957)", genres: ["Drama"], userRating: 5.0, rating: 5.0, timestamp: 1147868839 },
        { movieId: 4144, title: "In the Mood for Love (2000)", genres: ["Drama", "Romance"], userRating: 5.0, rating: 5.0, timestamp: 1147868898 }
      ]
    },
    user2: {
      id: "user2",
      userId: 2,
      name: "Sarah Jenkins",
      displayName: "Sarah Jenkins (Sci-Fi Explorer)",
      roleDescription: "Viễn tưởng & Phiêu lưu",
      avatarLetter: "S",
      avatarUrl: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&auto=format&fit=crop&q=80",
      bio: "Đam mê khám phá các vũ trụ viễn tưởng, không gian mạng Cyberpunk, phiêu lưu kỳ ảo và các cốt truyện du hành thời gian nghẹt thở.",
      ratingsCount: 142,
      meanRating: 4.25,
      activityLevel: "high",
      isInAlsTrain: true,
      defaultSliders: { depth: 0.70, pacing: 0.85, auteur: 0.65, tone: 0.75 },
      initialRatings: { 2571: 5.0, 79132: 5.0, 109487: 5.0, 589: 4.5, 260: 5.0, 33794: 5.0 },
      genreDistribution: {
        "Sci-Fi": 68, "Adventure": 54, "Action": 48, "Thriller": 32, "Fantasy": 28, "Mystery": 15, "Drama": 12
      },
      topFavoriteGenres: ["Sci-Fi", "Adventure", "Action", "Fantasy", "Thriller"],
      recentRatedMovies: [
        { movieId: 2571, title: "The Matrix (1999)", genres: ["Action", "Sci-Fi"], userRating: 5.0, rating: 5.0, timestamp: 1210000000 },
        { movieId: 79132, title: "Inception (2010)", genres: ["Action", "Crime", "Drama", "Mystery", "Sci-Fi", "Thriller"], userRating: 5.0, rating: 5.0, timestamp: 1285000000 },
        { movieId: 109487, title: "Interstellar (2014)", genres: ["Sci-Fi", "IMAX"], userRating: 5.0, rating: 5.0, timestamp: 1420000000 },
        { movieId: 260, title: "Star Wars: Episode IV - A New Hope (1977)", genres: ["Action", "Adventure", "Sci-Fi"], userRating: 5.0, rating: 5.0, timestamp: 1190000000 }
      ]
    },
    user_cold: {
      id: "user_cold",
      userId: 42,
      name: "Khán Giả 42",
      displayName: "Khán Giả 42 (Cold-Start)",
      roleDescription: "0 tương tác (Cold-Start)",
      avatarLetter: "4",
      avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
      bio: "Khán giả chưa có lịch sử đánh giá trong tập huấn luyện (Train), đóng vai trò kiểm chuẩn độ suy giảm ma trận ALS và cơ chế cứu cánh của Knowledge Graph.",
      ratingsCount: 0,
      meanRating: 0.0,
      activityLevel: "cold_start",
      isInAlsTrain: false,
      defaultSliders: { depth: 0.50, pacing: 0.50, auteur: 0.50, tone: 0.50 },
      initialRatings: {},
      genreDistribution: {},
      topFavoriteGenres: [],
      recentRatedMovies: []
    },
    user3: {
      id: "user3",
      userId: 3,
      name: "Marcus Vance",
      displayName: "Marcus Vance (Classic Crime)",
      roleDescription: "Hành động & Tội phạm kinh điển",
      avatarLetter: "M",
      avatarUrl: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop&q=80",
      bio: "Đam mê dòng phim tội phạm hình sự cổ điển, phim xã hội đen kinh điển và các tác phẩm hành động đỉnh cao.",
      ratingsCount: 89,
      meanRating: 4.10,
      activityLevel: "moderate",
      isInAlsTrain: true,
      defaultSliders: { depth: 0.65, pacing: 0.80, auteur: 0.60, tone: 0.40 },
      initialRatings: { 858: 5.0, 1221: 5.0, 296: 5.0, 4226: 4.5, 593: 5.0 },
      genreDistribution: { "Crime": 45, "Action": 38, "Drama": 30, "Thriller": 25 },
      topFavoriteGenres: ["Crime", "Action", "Drama", "Thriller"],
      recentRatedMovies: [
        { movieId: 858, title: "The Godfather (1972)", genres: ["Crime", "Drama"], userRating: 5.0, rating: 5.0 },
        { movieId: 1221, title: "The Godfather: Part II (1974)", genres: ["Crime", "Drama"], userRating: 5.0, rating: 5.0 }
      ]
    },
    user42: {
      id: "user42",
      userId: 42,
      name: "Khán Giả 42",
      displayName: "Khán Giả 42 (Cold-Start)",
      roleDescription: "0 tương tác (Cold-Start)",
      avatarLetter: "4",
      avatarUrl: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80",
      bio: "Khán giả chưa có lịch sử đánh giá trong tập huấn luyện (Train), đóng vai trò kiểm chuẩn độ suy giảm ma trận ALS và cơ chế cứu cánh của Knowledge Graph.",
      ratingsCount: 0,
      meanRating: 0.0,
      activityLevel: "cold_start",
      isInAlsTrain: false,
      defaultSliders: { depth: 0.50, pacing: 0.50, auteur: 0.50, tone: 0.50 },
      initialRatings: {},
      genreDistribution: {},
      topFavoriteGenres: [],
      recentRatedMovies: []
    },
    live_session: {
      id: "live_session",
      userId: 999,
      name: "Tài Khoản Của Bạn",
      displayName: "Tài Khoản Của Bạn (Live Session)",
      roleDescription: "Đánh giá trực tiếp",
      avatarLetter: "🎬",
      avatarUrl: "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200&auto=format&fit=crop&q=80",
      bio: "Phiên tương tác trực tiếp: Điểm số và sở thích cập nhật ngay lập tức khi bạn đánh giá phim ở Trang 1.",
      ratingsCount: 0,
      meanRating: 0.0,
      activityLevel: "live",
      isInAlsTrain: false,
      defaultSliders: { depth: 0.50, pacing: 0.50, auteur: 0.50, tone: 0.50 },
      initialRatings: {},
      genreDistribution: {},
      topFavoriteGenres: [],
      recentRatedMovies: []
    }
  };

  const TEST_USERS = [
    {
      userId: 1,
      name: "Khán giả 1 — Cinephile Auteur Enthusiast",
      description: "68 phim Train, điểm TB 3.78★ (Khắt khe, gu nghệ thuật châu Âu)",
      type: "active"
    },
    {
      userId: 2,
      name: "Khán giả 2 — Sci-Fi & Cyberpunk Explorer",
      description: "142 phim Train, điểm TB 4.25★ (Thích The Matrix, Inception, Interstellar)",
      type: "active"
    },
    {
      userId: 3,
      name: "Khán giả 3 — Classic Crime & Film-Noir Aficionado",
      description: "89 phim Train, điểm TB 4.10★ (Thích The Godfather, The Third Man)",
      type: "active"
    },
    {
      userId: 42,
      name: "Khán giả 42 — Cold-Start User (Tài khoản mới)",
      description: "0 đánh giá trong Train (Đã chọn Onboarding: Drama + Mind-bending)",
      type: "cold_start"
    }
  ];

  // =========================================================================
  // 4. TOP-N GỢI Ý CHO USER 1 KÈM 4 LOẠI THẺ PROVENANCE TYPING
  // =========================================================================
  const RECOMMENDATIONS_MODE_A = [
    {
      rank: 1,
      movieId: 318,
      title: "The Shawshank Redemption (1994)",
      releaseYear: 1994,
      genres: ["Crime", "Drama"],
      hybridScore: 0.0328,
      sources: ["ALS", "KG"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.85,
          text: "Trùng khớp thể loại Crime và Drama với tác phẩm bạn chấm 5.0★ 'City of God'."
        },
        {
          type: "LATENT_AFFINITY",
          label: "Nhân Tử Tiềm Ẩn ALS",
          colorCode: "#F43F5E",
          evidenceType: "LATENT_FACTOR_AFFINITY",
          status: "VERIFIED_NUMERICAL_PROJECTION",
          isHeuristic: false,
          dotProduct: 4.412,
          percentile: "Top 2%",
          text: "Điểm tích vô hướng vector thẩm mỹ đạt 4.412 (thuộc top 2% tương đồng cao nhất toàn danh mục)."
        }
      ]
    },
    {
      rank: 2,
      movieId: 858,
      title: "The Godfather (1972)",
      releaseYear: 1972,
      genres: ["Crime", "Drama"],
      hybridScore: 0.0315,
      sources: ["ALS", "KG"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.78,
          text: "Chia sẻ thể loại Crime và Drama kinh điển với các phim yêu thích trong lịch sử của bạn."
        },
        {
          type: "P3_COLLABORATIVE",
          label: "Đồng Tương Tác (P3)",
          colorCode: "#F97316",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.72,
          peerUserId: 1405,
          text: "Người dùng đồng gu #1405 trong cộng đồng đã chấm điểm tối đa 5.0★ cho cả 'The Godfather' và 'City of God'."
        }
      ]
    },
    {
      rank: 3,
      movieId: 1208,
      title: "Apocalypse Now (1979)",
      releaseYear: 1979,
      genres: ["Action", "Drama", "War"],
      hybridScore: 0.0294,
      sources: ["KG"],
      provenanceTags: [
        {
          type: "P2_GENOME",
          label: "Tâm Trạng / Genome (P2)",
          colorCode: "#14B8A6",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          targetRelevance: 0.892,
          text: "Chia sẻ các thẻ tâm trạng 'philosophical', 'existential', 'dark' với kiệt tác 'The Seventh Seal'."
        },
        {
          type: "LATENT_AFFINITY",
          label: "Nhân Tử Tiềm Ẩn ALS",
          colorCode: "#F43F5E",
          evidenceType: "LATENT_FACTOR_AFFINITY",
          status: "VERIFIED_NUMERICAL_PROJECTION",
          isHeuristic: false,
          dotProduct: 4.095,
          percentile: "Top 8%",
          text: "Vector tiềm ẩn ALS đạt 4.095, tương thích sâu sắc với gu điện ảnh chiến tranh triết lý của bạn."
        }
      ]
    },
    {
      rank: 4,
      movieId: 50,
      title: "The Usual Suspects (1995)",
      releaseYear: 1995,
      genres: ["Crime", "Mystery", "Thriller"],
      hybridScore: 0.0282,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.65,
          text: "Trùng khớp thể loại Crime và Mystery kịch tính với 'The Third Man'."
        },
        {
          type: "P3_COLLABORATIVE",
          label: "Đồng Tương Tác (P3)",
          colorCode: "#F97316",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.81,
          peerUserId: 892,
          text: "Người dùng #892 có lịch sử tương đồng 91% với bạn đã đánh giá 5.0★ cho tác phẩm này."
        }
      ]
    },
    {
      rank: 5,
      movieId: 527,
      title: "Schindler's List (1993)",
      releaseYear: 1993,
      genres: ["Drama", "War"],
      hybridScore: 0.0275,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.90,
          text: "Cùng thể loại Drama và War sâu sắc với 'Paths of Glory' và 'Ran'."
        },
        {
          type: "LATENT_AFFINITY",
          label: "Nhân Tử Tiềm Ẩn ALS",
          colorCode: "#F43F5E",
          evidenceType: "LATENT_FACTOR_AFFINITY",
          status: "VERIFIED_NUMERICAL_PROJECTION",
          isHeuristic: false,
          dotProduct: 4.251,
          percentile: "Top 4%",
          text: "Điểm tích vô hướng 4.251, xếp thứ 4 trong không gian sở thích của mô hình Spark ALS."
        }
      ]
    },
    {
      rank: 6,
      movieId: 1221,
      title: "The Godfather: Part II (1974)",
      releaseYear: 1974,
      genres: ["Crime", "Drama"],
      hybridScore: 0.0269,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.85,
          text: "Đồng điệu thể loại Crime và Drama với các tác phẩm kinh điển mà bạn yêu thích."
        },
        {
          type: "P3_COLLABORATIVE",
          label: "Đồng Tương Tác (P3)",
          colorCode: "#F97316",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.74,
          peerUserId: 1405,
          text: "Người dùng #1405 cùng nhóm khán giả khó tính đánh giá 5.0★ cho phần tiếp nối vĩ đại này."
        }
      ]
    },
    {
      rank: 7,
      movieId: 1193,
      title: "One Flew Over the Cuckoo's Nest (1975)",
      releaseYear: 1975,
      genres: ["Drama"],
      hybridScore: 0.0261,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P2_GENOME",
          label: "Tâm Trạng / Genome (P2)",
          colorCode: "#14B8A6",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          targetRelevance: 0.875,
          text: "Có chung các thẻ tâm lý 'rebellion', 'bittersweet', 'social commentary' với 'Three Colors: Blue'."
        },
        {
          type: "LATENT_AFFINITY",
          label: "Nhân Tử Tiềm Ẩn ALS",
          colorCode: "#F43F5E",
          evidenceType: "LATENT_FACTOR_AFFINITY",
          status: "VERIFIED_NUMERICAL_PROJECTION",
          isHeuristic: false,
          dotProduct: 4.180,
          percentile: "Top 6%",
          text: "Mô hình ALS dự đoán điểm số 4.180 dựa trên sự cộng hưởng tâm lý của Khán giả 1."
        }
      ]
    },
    {
      rank: 8,
      movieId: 912,
      title: "Casablanca (1942)",
      releaseYear: 1942,
      genres: ["Drama", "Romance"],
      hybridScore: 0.0255,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.92,
          text: "Chia sẻ hai thể loại cốt lõi Drama và Romance với kiệt tác 'In the Mood for Love' (5.0★)."
        },
        {
          type: "P2_GENOME",
          label: "Tâm Trạng / Genome (P2)",
          colorCode: "#14B8A6",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          targetRelevance: 0.840,
          text: "Chia sẻ thẻ tâm trạng hoài niệm 'melancholic' và 'unrequited love' rất đậm nét."
        }
      ]
    },
    {
      rank: 9,
      movieId: 904,
      title: "Rear Window (1954)",
      releaseYear: 1954,
      genres: ["Mystery", "Thriller"],
      hybridScore: 0.0248,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P2_GENOME",
          label: "Tâm Trạng / Genome (P2)",
          colorCode: "#14B8A6",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          targetRelevance: 0.865,
          text: "Sở hữu các thẻ gen căng thẳng 'suspense', 'clever', 'voyeurism' tương tự các phim giật gân kinh điển."
        },
        {
          type: "P3_COLLABORATIVE",
          label: "Đồng Tương Tác (P3)",
          colorCode: "#F97316",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.68,
          peerUserId: 642,
          text: "Người dùng #642 yêu thích phim nghệ thuật kinh điển đã chấm 4.5★ cho tác phẩm của Hitchcock."
        }
      ]
    },
    {
      rank: 10,
      movieId: 1213,
      title: "Goodfellas (1990)",
      releaseYear: 1990,
      genres: ["Crime", "Drama"],
      hybridScore: 0.0240,
      sources: ["ALS"],
      provenanceTags: [
        {
          type: "P1_GENRE",
          label: "Đồng Thể Loại (P1)",
          colorCode: "#D97706",
          evidenceType: "DIRECT_GRAPH_TRAVERSAL",
          status: "VERIFIED_GROUND_TRUTH",
          isHeuristic: false,
          scoreContribution: 0.80,
          text: "Trùng khớp thể loại Crime và Drama với lịch sử đánh giá phim tội phạm của bạn."
        },
        {
          type: "LATENT_AFFINITY",
          label: "Nhân Tử Tiềm Ẩn ALS",
          colorCode: "#F43F5E",
          evidenceType: "LATENT_FACTOR_AFFINITY",
          status: "VERIFIED_NUMERICAL_PROJECTION",
          isHeuristic: false,
          dotProduct: 4.050,
          percentile: "Top 9%",
          text: "Điểm chiếu ALS 4.050, củng cố mức độ yêu thích dòng phim băng đảng có chiều sâu."
        }
      ]
    }
  ];

  // =========================================================================
  // 5. TOP-10 ĐỐI ĐẦU SONG SONG GIỮA 5 MÔ HÌNH (MODE B BENCHMARK)
  // =========================================================================
  const MODELS_METADATA = {
    als: {
      id: "als",
      name: "Spark ALS Collaborative",
      badgeText: "SPARK ALS",
      color: "sky",
      hexColor: "#0284C7",
      executionTimeMs: 3.28,
      algorithm: "Matrix Factorization (Rank=8, Reg=0.3, Iter=10)",
      description: "Phân tích nhân tử tiềm ẩn trên cụm Apache Spark, đo bằng tích vô hướng vector",
      noveltyBitsAvg: 7.85,
      longTailRatio: 0.20
    },
    kg: {
      id: "kg",
      name: "Knowledge Graph Multi-Hop",
      badgeText: "KG IN-MEMORY",
      color: "emerald",
      hexColor: "#10B981",
      executionTimeMs: 3.63,
      algorithm: "Metapath Random Walk (P1 Genre + P2 Mood/Genome + P3 Co-rating)",
      description: "Suy luận ngữ nghĩa đa bước trên đồ thị tri thức, khai phá phim ngách có giải thích",
      noveltyBitsAvg: 9.14,
      longTailRatio: 0.60
    },
    hybrid_rrf: {
      id: "hybrid_rrf",
      name: "Hybrid RRF (k=60)",
      badgeText: "HYBRID RRF",
      color: "amber",
      hexColor: "#D97706",
      executionTimeMs: 3.08,
      algorithm: "Reciprocal Rank Fusion phi tham số (Cormack et al., k=60)",
      description: "Dung hợp thứ hạng nghịch đảo, bất biến thang điểm thô, cân bằng chính xác và độ phủ",
      noveltyBitsAvg: 8.36,
      longTailRatio: 0.40
    },
    hybrid_weighted: {
      id: "hybrid_weighted",
      name: "Hybrid Weighted (50/50)",
      badgeText: "WEIGHTED 50/50",
      color: "amber",
      hexColor: "#F59E0B",
      executionTimeMs: 2.88,
      algorithm: "Min-Max Normalized Linear Combination (0.5 ALS + 0.5 KG)",
      description: "Dung hợp điểm số tuyến tính chuẩn hóa, cho phép kéo trượt trọng số thực nghiệm",
      noveltyBitsAvg: 9.02,
      longTailRatio: 0.55
    },
    popularity: {
      id: "popularity",
      name: "Popularity Baseline (M03)",
      badgeText: "POPULARITY BASELINE",
      color: "rose",
      hexColor: "#F43F5E",
      executionTimeMs: 0.025,
      algorithm: "Global Ratings Frequency Ranking (min 50 ratings)",
      description: "Mốc tham chiếu tần suất toàn cục không cá nhân hóa và cơ chế cứu cánh Cold-start",
      noveltyBitsAvg: 3.42,
      longTailRatio: 0.00
    }
  };

  const TOP_10_BY_MODEL = {
    als: [
      { rank: 1, movieId: 318, title: "The Shawshank Redemption (1994)", score: 4.412, rawScoreText: "4.4120", primaryGenre: "Drama", consensusCount: 5 },
      { rank: 2, movieId: 858, title: "The Godfather (1972)", score: 4.385, rawScoreText: "4.3850", primaryGenre: "Crime", consensusCount: 4 },
      { rank: 3, movieId: 50, title: "The Usual Suspects (1995)", score: 4.298, rawScoreText: "4.2980", primaryGenre: "Mystery", consensusCount: 3 },
      { rank: 4, movieId: 527, title: "Schindler's List (1993)", score: 4.251, rawScoreText: "4.2510", primaryGenre: "Drama", consensusCount: 3 },
      { rank: 5, movieId: 1221, title: "The Godfather: Part II (1974)", score: 4.210, rawScoreText: "4.2100", primaryGenre: "Crime", consensusCount: 3 },
      { rank: 6, movieId: 1193, title: "One Flew Over the Cuckoo's Nest (1975)", score: 4.180, rawScoreText: "4.1800", primaryGenre: "Drama", consensusCount: 3 },
      { rank: 7, movieId: 912, title: "Casablanca (1942)", score: 4.150, rawScoreText: "4.1500", primaryGenre: "Romance", consensusCount: 3 },
      { rank: 8, movieId: 904, title: "Rear Window (1954)", score: 4.120, rawScoreText: "4.1200", primaryGenre: "Mystery", consensusCount: 3 },
      { rank: 9, movieId: 111, title: "Taxi Driver (1976)", score: 4.095, rawScoreText: "4.0950", primaryGenre: "Crime", consensusCount: 1 },
      { rank: 10, movieId: 1213, title: "Goodfellas (1990)", score: 4.050, rawScoreText: "4.0500", primaryGenre: "Crime", consensusCount: 3 }
    ],
    kg: [
      { rank: 1, movieId: 318, title: "The Shawshank Redemption (1994)", score: 0.892, rawScoreText: "0.8920", primaryGenre: "Drama", consensusCount: 5 },
      { rank: 2, movieId: 1208, title: "Apocalypse Now (1979)", score: 0.845, rawScoreText: "0.8450", primaryGenre: "War", consensusCount: 3 },
      { rank: 3, movieId: 1217, title: "Ran (1985)", score: 0.820, rawScoreText: "0.8200", primaryGenre: "Drama", consensusCount: 1 },
      { rank: 4, movieId: 1233, title: "The Boat (Das Boot) (1981)", score: 0.795, rawScoreText: "0.7950", primaryGenre: "War", consensusCount: 1 },
      { rank: 5, movieId: 3030, title: "Yojimbo (1961)", score: 0.760, rawScoreText: "0.7600", primaryGenre: "Action", consensusCount: 1 },
      { rank: 6, movieId: 1178, title: "Paths of Glory (1957)", score: 0.740, rawScoreText: "0.7400", primaryGenre: "War", consensusCount: 1 },
      { rank: 7, movieId: 926, title: "All About Eve (1950)", score: 0.715, rawScoreText: "0.7150", primaryGenre: "Drama", consensusCount: 1 },
      { rank: 8, movieId: 1212, title: "The Third Man (1949)", score: 0.690, rawScoreText: "0.6900", primaryGenre: "Film-Noir", consensusCount: 1 },
      { rank: 9, movieId: 1256, title: "Duck Soup (1933)", score: 0.670, rawScoreText: "0.6700", primaryGenre: "Comedy", consensusCount: 1 },
      { rank: 10, movieId: 858, title: "The Godfather (1972)", score: 0.650, rawScoreText: "0.6500", primaryGenre: "Crime", consensusCount: 4 }
    ],
    hybrid_rrf: [
      { rank: 1, movieId: 318, title: "The Shawshank Redemption (1994)", score: 0.0328, rawScoreText: "0.0328", primaryGenre: "Drama", consensusCount: 5 },
      { rank: 2, movieId: 858, title: "The Godfather (1972)", score: 0.0315, rawScoreText: "0.0315", primaryGenre: "Crime", consensusCount: 4 },
      { rank: 3, movieId: 1208, title: "Apocalypse Now (1979)", score: 0.0294, rawScoreText: "0.0294", primaryGenre: "War", consensusCount: 3 },
      { rank: 4, movieId: 50, title: "The Usual Suspects (1995)", score: 0.0282, rawScoreText: "0.0282", primaryGenre: "Mystery", consensusCount: 3 },
      { rank: 5, movieId: 527, title: "Schindler's List (1993)", score: 0.0275, rawScoreText: "0.0275", primaryGenre: "Drama", consensusCount: 3 },
      { rank: 6, movieId: 1221, title: "The Godfather: Part II (1974)", score: 0.0269, rawScoreText: "0.0269", primaryGenre: "Crime", consensusCount: 3 },
      { rank: 7, movieId: 1193, title: "One Flew Over the Cuckoo's Nest (1975)", score: 0.0261, rawScoreText: "0.0261", primaryGenre: "Drama", consensusCount: 3 },
      { rank: 8, movieId: 912, title: "Casablanca (1942)", score: 0.0255, rawScoreText: "0.0255", primaryGenre: "Romance", consensusCount: 3 },
      { rank: 9, movieId: 904, title: "Rear Window (1954)", score: 0.0248, rawScoreText: "0.0248", primaryGenre: "Mystery", consensusCount: 3 },
      { rank: 10, movieId: 1213, title: "Goodfellas (1990)", score: 0.0240, rawScoreText: "0.0240", primaryGenre: "Crime", consensusCount: 3 }
    ],
    hybrid_weighted: [
      { rank: 1, movieId: 318, title: "The Shawshank Redemption (1994)", score: 0.9450, rawScoreText: "0.9450", primaryGenre: "Drama", consensusCount: 5 },
      { rank: 2, movieId: 858, title: "The Godfather (1972)", score: 0.9120, rawScoreText: "0.9120", primaryGenre: "Crime", consensusCount: 4 },
      { rank: 3, movieId: 50, title: "The Usual Suspects (1995)", score: 0.8800, rawScoreText: "0.8800", primaryGenre: "Mystery", consensusCount: 3 },
      { rank: 4, movieId: 1208, title: "Apocalypse Now (1979)", score: 0.8650, rawScoreText: "0.8650", primaryGenre: "War", consensusCount: 3 },
      { rank: 5, movieId: 527, title: "Schindler's List (1993)", score: 0.8500, rawScoreText: "0.8500", primaryGenre: "Drama", consensusCount: 3 },
      { rank: 6, movieId: 1221, title: "The Godfather: Part II (1974)", score: 0.8300, rawScoreText: "0.8300", primaryGenre: "Crime", consensusCount: 3 },
      { rank: 7, movieId: 1193, title: "One Flew Over the Cuckoo's Nest (1975)", score: 0.8100, rawScoreText: "0.8100", primaryGenre: "Drama", consensusCount: 3 },
      { rank: 8, movieId: 912, title: "Casablanca (1942)", score: 0.7900, rawScoreText: "0.7900", primaryGenre: "Romance", consensusCount: 3 },
      { rank: 9, movieId: 904, title: "Rear Window (1954)", score: 0.7700, rawScoreText: "0.7700", primaryGenre: "Mystery", consensusCount: 3 },
      { rank: 10, movieId: 1213, title: "Goodfellas (1990)", score: 0.7500, rawScoreText: "0.7500", primaryGenre: "Crime", consensusCount: 3 }
    ],
    popularity: [
      { rank: 1, movieId: 318, title: "The Shawshank Redemption (1994)", score: 80448, rawScoreText: "80,448", primaryGenre: "Drama", consensusCount: 5 },
      { rank: 2, movieId: 356, title: "Forrest Gump (1994)", score: 80375, rawScoreText: "80,375", primaryGenre: "Drama", consensusCount: 1 },
      { rank: 3, movieId: 593, title: "The Silence of the Lambs (1991)", score: 73109, rawScoreText: "73,109", primaryGenre: "Thriller", consensusCount: 1 },
      { rank: 4, movieId: 2571, title: "The Matrix (1999)", score: 71787, rawScoreText: "71,787", primaryGenre: "Sci-Fi", consensusCount: 1 },
      { rank: 5, movieId: 260, title: "Star Wars: Episode IV (1977)", score: 68083, rawScoreText: "68,083", primaryGenre: "Adventure", consensusCount: 1 },
      { rank: 6, movieId: 480, title: "Jurassic Park (1993)", score: 63268, rawScoreText: "63,268", primaryGenre: "Adventure", consensusCount: 1 },
      { rank: 7, movieId: 110, title: "Braveheart (1995)", score: 58266, rawScoreText: "58,266", primaryGenre: "Action", consensusCount: 1 },
      { rank: 8, movieId: 589, title: "Terminator 2: Judgment Day (1991)", score: 57379, rawScoreText: "57,379", primaryGenre: "Action", consensusCount: 1 },
      { rank: 9, movieId: 1, title: "Toy Story (1995)", score: 57342, rawScoreText: "57,342", primaryGenre: "Animation", consensusCount: 1 },
      { rank: 10, movieId: 4993, title: "The Lord of the Rings: Fellowship (2001)", score: 56400, rawScoreText: "56,400", primaryGenre: "Fantasy", consensusCount: 1 }
    ]
  };

  // =========================================================================
  // 6. MA TRẬN TƯƠNG QUAN SPEARMAN [-1.0, 1.0] VÀ TƯƠNG ĐỒNG JACCARD [0.0, 1.0]
  // =========================================================================
  const PAIRWISE_OVERLAPS = [
    {
      modelA: "als",
      modelB: "kg",
      commonCount: 2,
      jaccard: 0.1111, // 2 / 18
      spearman: 1.0000,
      commonMovieIds: [318, 858],
      scientificNote: "k=2 phim chung; ALS và KG bổ trợ lẫn nhau với độ trùng lặp tập hợp 11.1%, Spearman đạt +1.00."
    },
    {
      modelA: "als",
      modelB: "hybrid_rrf",
      commonCount: 9,
      jaccard: 0.8182, // 9 / 11
      spearman: 1.0000,
      commonMovieIds: [318, 858, 50, 527, 1221, 1193, 912, 904, 1213],
      scientificNote: "Đồng thuận cực cao (81.8% Jaccard, Spearman +1.00); RRF kế thừa ổn định các ứng viên chất lượng từ ALS."
    },
    {
      modelA: "als",
      modelB: "hybrid_weighted",
      commonCount: 9,
      jaccard: 0.8182,
      spearman: 1.0000,
      commonMovieIds: [318, 858, 50, 527, 1221, 1193, 912, 904, 1213],
      scientificNote: "Tương quan thứ hạng Spearman đạt +1.0000, Weighted 50/50 phản ánh trật tự xếp hạng mạnh mẽ của ALS."
    },
    {
      modelA: "als",
      modelB: "popularity",
      commonCount: 1,
      jaccard: 0.0526, // 1 / 19 ≈ 0.0526
      spearman: null, // k < 2 bắt buộc trả về null theo quy tắc bất biến toán học
      commonMovieIds: [318],
      scientificNote: "k=1 phim chung (The Shawshank Redemption) -> Jaccard = 1/19 ≈ 0.0526; Spearman bắt buộc trả về null (vì k < 2 không thể xếp cặp thứ hạng); ALS cá nhân hóa cao đối nghịch Popularity đại chúng."
    },
    {
      modelA: "kg",
      modelB: "hybrid_rrf",
      commonCount: 3,
      jaccard: 0.1765,
      spearman: 0.5000,
      commonMovieIds: [318, 858, 1208],
      scientificNote: "RRF k=60 kéo được 3 ứng viên xuất sắc từ KG vào Top-10 dù điểm thô của KG nhỏ hơn ALS rất nhiều."
    },
    {
      modelA: "kg",
      modelB: "hybrid_weighted",
      commonCount: 3,
      jaccard: 0.1765,
      spearman: 0.5000,
      commonMovieIds: [318, 858, 1208],
      scientificNote: "Weighted kết hợp tuyến tính giúp duy trì 3 bộ phim cốt lõi từ đồ thị tri thức."
    },
    {
      modelA: "kg",
      modelB: "popularity",
      commonCount: 1,
      jaccard: 0.0526, // 1 / 19
      spearman: null,
      commonMovieIds: [318],
      scientificNote: "k=1 phim chung (The Shawshank Redemption) -> Jaccard = 1/19 ≈ 0.0526, Spearman=null. KG tập trung ngữ nghĩa điện ảnh chuyên sâu."
    },
    {
      modelA: "hybrid_rrf",
      modelB: "hybrid_weighted",
      commonCount: 10,
      jaccard: 1.0000,
      spearman: 0.9879,
      commonMovieIds: [318, 858, 1208, 50, 527, 1221, 1193, 912, 904, 1213],
      scientificNote: "Hai chiến lược dung hợp đề xuất cùng 10 bộ phim với thứ tự gần như tuyệt đối (Spearman +0.9879)."
    },
    {
      modelA: "hybrid_rrf",
      modelB: "popularity",
      commonCount: 1,
      jaccard: 0.0526,
      spearman: null,
      commonMovieIds: [318],
      scientificNote: "k=1 phim chung (The Shawshank Redemption) -> Jaccard = 1/19 ≈ 0.0526, Spearman=null. RRF duy trì độ tinh khiết cá nhân hóa cao."
    },
    {
      modelA: "hybrid_weighted",
      modelB: "popularity",
      commonCount: 1,
      jaccard: 0.0526,
      spearman: null,
      commonMovieIds: [318],
      scientificNote: "k=1 phim chung (The Shawshank Redemption) -> Jaccard = 1/19 ≈ 0.0526, Spearman=null. Weighted giữ vững tính cá nhân hóa."
    }
  ];

  // Ma trận dạng bảng 5x5 tiện vẽ Heatmap
  const CORRELATION_MATRIX = {
    models: ["als", "kg", "hybrid_rrf", "hybrid_weighted", "popularity"],
    spearman: [
      [1.0000, 1.0000, 1.0000, 1.0000, null],
      [1.0000, 1.0000, 0.5000, 0.5000, null],
      [1.0000, 0.5000, 1.0000, 0.9879, null],
      [1.0000, 0.5000, 0.9879, 1.0000, null],
      [null,   null,   null,   null,   1.0000]
    ],
    jaccard: [
      [1.0000, 0.1111, 0.8182, 0.8182, 0.0526],
      [0.1111, 1.0000, 0.1765, 0.1765, 0.0526],
      [0.8182, 0.1765, 1.0000, 1.0000, 0.0526],
      [0.8182, 0.1765, 1.0000, 1.0000, 0.0526],
      [0.0526, 0.0526, 0.0526, 0.0526, 1.0000]
    ],
    commonCounts: [
      [10, 2,  9,  9,  1],
      [2,  10, 3,  3,  1],
      [9,  3,  10, 10, 1],
      [9,  3,  10, 10, 1],
      [1,  1,  1,  1,  10]
    ]
  };

  // =========================================================================
  // 7. DỮ LIỆU ĐỊNH LƯỢNG KỊCH BẢN COLD-START VÀ LONG-TAIL
  // =========================================================================
  const COLD_START_DATA = {
    scenarios: [
      {
        id: "zero_history",
        name: "Người dùng mới hoàn toàn (Zero-History User)",
        description: "Khách hàng mới tạo tài khoản, có 0 lượt đánh giá trong Train (chỉ chọn tag onboarding)",
        modelResponses: {
          als: { status: "FAIL / DROPPED", fallback: "Chuyển hướng sang Popularity", latencyMs: 0.1, degradationPct: 100 },
          kg: { status: "ACTIVE (1-Hop Ontology)", fallback: "Không cần fallback (khai phá qua Genre/Mood)", latencyMs: 3.2, degradationPct: 24 },
          hybrid_rrf: { status: "GRACEFUL DEGRADATION", fallback: "Tự động trôi về KG / Popularity", latencyMs: 3.4, degradationPct: 18 },
          hybrid_weighted: { status: "IMPUTATION ACTIVE", fallback: "Bù giá trị trung vị cho ALS", latencyMs: 3.1, degradationPct: 22 },
          popularity: { status: "100% IMMUNE", fallback: "Không áp dụng", latencyMs: 0.02, degradationPct: 0 }
        }
      },
      {
        id: "sparsity_test",
        name: "Thử nghiệm độ thưa thớt (Sparsity Degradation N=1..50)",
        description: "Đo lường sự sụt giảm hiệu năng NDCG@10 khi rút gọn lịch sử tương tác từ 50 xuống 1 đánh giá",
        curvePoints: [
          { ratingsCount: 50, alsNdcg: 0.078, kgNdcg: 0.062, rrfNdcg: 0.082, popNdcg: 0.043 },
          { ratingsCount: 20, alsNdcg: 0.061, kgNdcg: 0.058, rrfNdcg: 0.071, popNdcg: 0.043 },
          { ratingsCount: 10, alsNdcg: 0.038, kgNdcg: 0.054, rrfNdcg: 0.059, popNdcg: 0.043 },
          { ratingsCount: 5,  alsNdcg: 0.015, kgNdcg: 0.051, rrfNdcg: 0.048, popNdcg: 0.043 },
          { ratingsCount: 3,  alsNdcg: 0.005, kgNdcg: 0.049, rrfNdcg: 0.044, popNdcg: 0.043 },
          { ratingsCount: 1,  alsNdcg: 0.000, kgNdcg: 0.046, rrfNdcg: 0.041, popNdcg: 0.043 },
          { ratingsCount: 0,  alsNdcg: 0.000, kgNdcg: 0.041, rrfNdcg: 0.043, popNdcg: 0.043 }
        ]
      },
      {
        id: "unrated_items",
        name: "Phim mới nhập vào hệ thống (0 Rating Item Cold-Start)",
        description: "Khả năng giới thiệu một tác phẩm điện ảnh vừa ra mắt chưa nhận được lượt tương tác nào",
        modelResponses: {
          als: { status: "BLOCKED", text: "Bất lực hoàn toàn, phải chờ đợt huấn luyện lại ma trận theo chu kỳ đêm" },
          kg: { status: "READY", text: "Đề xuất tức thì qua các cạnh tĩnh IN_GENRE, HAS_GENOME_TAG, DIRECTED_BY" },
          hybrid_rrf: { status: "READY", text: "Đưa phim mới lên qua nhánh KG mà không làm sập pipeline" },
          hybrid_weighted: { status: "READY", text: "Áp dụng chiến lược source_aware imputation" },
          popularity: { status: "BLOCKED", text: "Không thể đề xuất vì số lượt đánh giá bằng 0" }
        }
      }
    ],
    get sparsityDegradation() {
      return this.scenarios && this.scenarios[1] ? this.scenarios[1].curvePoints : [];
    }
  };

  const LONG_TAIL_DATA = {
    overview: {
      catalogSize: 62423,
      shortHeadBoundaryPct: 20,
      shortHeadInteractionSharePct: 80,
      evaluationCohortUsers: 200
    },
    coverageMetrics: [
      { modelId: "popularity", modelName: "Popularity Baseline", coverageAt10: 55, coverageAt20: 90, noveltyBitsAvg: 3.42, giniIndex: 0.912, shortHeadRatio: 1.00, longTailRatio: 0.00 },
      { modelId: "als", modelName: "Spark ALS Champion", coverageAt10: 14, coverageAt20: 32, noveltyBitsAvg: 7.85, giniIndex: 0.884, shortHeadRatio: 0.80, longTailRatio: 0.20 },
      { modelId: "hybrid_rrf", modelName: "Hybrid RRF (k=60)", coverageAt10: 239, coverageAt20: 428, noveltyBitsAvg: 8.36, giniIndex: 0.528, shortHeadRatio: 0.60, longTailRatio: 0.40 },
      { modelId: "hybrid_weighted", modelName: "Hybrid Weighted (50/50)", coverageAt10: 295, coverageAt20: 539, noveltyBitsAvg: 9.02, giniIndex: 0.435, shortHeadRatio: 0.45, longTailRatio: 0.55 },
      { modelId: "kg", modelName: "Knowledge Graph (P1+P2+P3)", coverageAt10: 414, coverageAt20: 693, noveltyBitsAvg: 9.14, giniIndex: 0.412, shortHeadRatio: 0.40, longTailRatio: 0.60 }
    ],
    scientificInsight: "Phát hiện cốt lõi: Knowledge Graph đạt độ phủ danh mục gấp 7.5 lần Popularity (414 vs 55 phim @10) và Novelty đạt 9.14 bits. Hybrid RRF đạt tỷ lệ vàng 60% Short-head / 40% Long-tail, kết hợp hoàn hảo giữa tính quen thuộc tin cậy và sự mới lạ khám phá."
  };

  // =========================================================================
  // 8. BẢNG CHỈ SỐ KIỂM CHUẨN OFFLINE THỰC NGHIỆM (PHASE 4 EXPANDED VALIDATION)
  // =========================================================================
  const OFFLINE_BENCHMARKS = {
    cohortDescription: "Đo lường trên đoàn hệ 132 người dùng có đánh giá tích cực (Temporal Leave-1-Last Split)",
    academicFootnote: "Ghi chú học thuật: Thuật toán ALS đơn lẻ gặp thách thức ma trận cực thưa trên giao thức Temporal Leave-1-Last. Đây chính là động lực khoa học cốt lõi thúc đẩy phát triển Mô hình Lai Hybrid RRF (kết hợp Đồ thị tri thức KG), nâng Hit Rate@10 từ 0.00% lên 8.33% (đạt 9.85% ở KG) và mở rộng độ bao phủ danh mục lên 239/250 phim (95.6% danh mục, gấp 17 lần ALS thuần túy và gấp 4.3 lần Popularity). Chỉ số Độ mới lạ (Novelty) được định lượng theo đơn vị bits thông tin entropy (Shannon self-information) đối với tần suất xuất hiện trong tập huấn luyện.",
    metrics: [
      { metric: "HR@5", name: "Hit Rate @ 5", als: 0.0000, kg: 0.0833, rrf: 0.0606, weighted: 0.0606, pop: 0.0379, best: "KG" },
      { metric: "NDCG@5", name: "Normalized DCG @ 5", als: 0.0000, kg: 0.0447, rrf: 0.0277, weighted: 0.0270, pop: 0.0294, best: "KG" },
      { metric: "MRR@5", name: "Mean Reciprocal Rank @ 5", als: 0.0000, kg: 0.0318, rrf: 0.0172, weighted: 0.0163, pop: 0.0268, best: "KG" },
      { metric: "HR@10", name: "Hit Rate @ 10", als: 0.0000, kg: 0.0985, rrf: 0.0833, weighted: 0.0909, pop: 0.0833, best: "KG" },
      { metric: "NDCG@10", name: "Normalized DCG @ 10", als: 0.0000, kg: 0.0497, rrf: 0.0351, weighted: 0.0367, pop: 0.0437, best: "KG" },
      { metric: "MRR@10", name: "Mean Reciprocal Rank @ 10", als: 0.0000, kg: 0.0339, rrf: 0.0202, weighted: 0.0202, pop: 0.0324, best: "KG" },
      { metric: "HR@20", name: "Hit Rate @ 20", als: 0.0000, kg: 0.1439, rrf: 0.0985, weighted: 0.1136, pop: 0.1136, best: "KG" },
      { metric: "NDCG@20", name: "Normalized DCG @ 20", als: 0.0000, kg: 0.0609, rrf: 0.0390, weighted: 0.0422, pop: 0.0512, best: "KG" },
      { metric: "MRR@20", name: "Mean Reciprocal Rank @ 20", als: 0.0000, kg: 0.0369, rrf: 0.0213, weighted: 0.0216, pop: 0.0343, best: "KG" },
      { metric: "Coverage@10", name: "Catalog Coverage @ 10 (Unique Items)", als: 14, kg: 414, rrf: 239, weighted: 295, pop: 55, best: "KG" },
      { metric: "Coverage@20", name: "Catalog Coverage @ 20 (Unique Items)", als: 32, kg: 693, rrf: 428, weighted: 539, pop: 90, best: "KG" },
      { metric: "Latency_P95", name: "Độ trễ suy luận P95 (Warm)", als: "2.5 ms", kg: "3.6 ms", rrf: "3.1 ms", weighted: "2.9 ms", pop: "< 0.1 ms", best: "Popularity" }
    ]
  };

  // =========================================================================
  // 8.1 BỘ TÍNH ĐIỂM GỢI Ý ĐỘNG THỜI GIAN THỰC (CLIENT-SIDE RECOMMENDATION ENGINE)
  // Tính điểm tức thì < 5ms (60 FPS) theo Vector Gu Sliders & Mood Selector
  // =========================================================================
  const MoodEngine = {
    /**
     * Tính toán điểm số tương thích động thời gian thực cho từng bộ phim trong catalog dựa trên vector thanh trượt sở thích, bộ lọc tâm trạng và thể loại khuếch đại (vòng lặp kín).
     * Thuật toán kết hợp độ tương đồng Cosine giữa vector người dùng và tasteFeatures của phim, điểm đánh giá trung bình, thưởng tâm trạng và thưởng thể loại.
     * @param {Object} sliders - Tọa độ thanh trượt sở thích (depth, pacing, auteur, tone)
     * @param {string} selectedMood - Tâm trạng được chọn ('all', 'mind_bending', 'adrenaline_rush', ...)
     * @param {Array<Object>} [targetCatalog] - Danh mục phim cần tính điểm (mặc định là CATALOG)
     * @param {Object} [options] - Tùy chọn nâng cao (boostedGenres, favoriteGenres, isColdStart)
     * @returns {Array<Object>} Danh sách phim đã được gán điểm động và sắp xếp giảm dần theo dynamicScore
     */
    calculateDynamicScores: function(sliders, selectedMood, targetCatalog, options) {
      const catalog = targetCatalog || CATALOG;
      const opts = options || {};
      const boostedGenres = Array.isArray(opts.boostedGenres) ? opts.boostedGenres : [];
      const favoriteGenres = Array.isArray(opts.favoriteGenres) ? opts.favoriteGenres : [];
      const isColdStart = Boolean(opts.isColdStart);

      const s = {
        depth: (sliders && typeof sliders.depth === 'number') ? sliders.depth : 0.75,
        pacing: (sliders && typeof sliders.pacing === 'number') ? sliders.pacing : 0.60,
        auteur: (sliders && typeof sliders.auteur === 'number') ? sliders.auteur : 0.85,
        tone: (sliders && typeof sliders.tone === 'number') ? sliders.tone : 0.50
      };

      const normS = Math.sqrt(s.depth ** 2 + s.pacing ** 2 + s.auteur ** 2 + s.tone ** 2) || 1e-6;

      const scoredMovies = catalog.map(movie => {
        const tf = movie.tasteFeatures || { depth: 0.8, pacing: 0.6, auteur: 0.8, tone: 0.5 };
        const dot = (s.depth * tf.depth) + (s.pacing * tf.pacing) + (s.auteur * tf.auteur) + (s.tone * tf.tone);
        const normM = Math.sqrt(tf.depth ** 2 + tf.pacing ** 2 + tf.auteur ** 2 + tf.tone ** 2) || 1e-6;
        const cosine = dot / (normS * normM);

        const baseScore = (movie.ratingAvg || 4.0) / 5.0;

        let moodBonus = 0.0;
        if (selectedMood && selectedMood !== 'all') {
          if (movie.primaryMood === selectedMood) {
            moodBonus = 0.20;
          }
        }

        // Tương thích thể loại phản hồi động (Closed-Loop Feedback Bonus)
        let genreBonus = 0.0;
        if (movie.genres && Array.isArray(movie.genres)) {
          // Thưởng nóng thể loại vừa được chấm 4-5 sao gần nhất
          if (boostedGenres.length > 0 && movie.genres.some(g => boostedGenres.includes(g))) {
            genreBonus += 0.22;
          }
          // Thưởng theo gu thể loại yêu thích của người dùng hiện tại
          if (favoriteGenres.length > 0 && movie.genres.some(g => favoriteGenres.includes(g))) {
            genreBonus += 0.08;
          }
        }

        let matchScore = (0.35 * baseScore) + (0.40 * Math.max(0, cosine)) + (0.15 * moodBonus) + (0.10 * Math.min(1.0, genreBonus));

        // Nếu là kịch bản Cold-Start: người dùng mới 0 tương tác -> ưu tiên phim có độ phổ biến toàn cục & KG coverage
        if (isColdStart) {
          const popFactor = Math.min(1.0, (movie.ratingCount || 1000) / 80500);
          matchScore = (0.45 * matchScore) + (0.55 * popFactor);
        }

        const compatibilityPct = Math.round(Math.min(99, Math.max(65, matchScore * 100)));

        return Object.assign({}, movie, {
          dynamicScore: matchScore,
          compatibilityPct: compatibilityPct,
          cosineSimilarity: cosine,
          isMoodMatch: Boolean(selectedMood && movie.primaryMood === selectedMood),
          isGenreBoosted: Boolean(boostedGenres.length > 0 && movie.genres && movie.genres.some(g => boostedGenres.includes(g)))
        });
      });

      scoredMovies.sort((a, b) => {
        if (b.dynamicScore !== a.dynamicScore) {
          return b.dynamicScore - a.dynamicScore;
        }
        return (b.ratingCount || 0) - (a.ratingCount || 0);
      });

      return scoredMovies;
    }
  };

  // =========================================================================
  // 9. ĐÓNG GÓI ĐỐI TƯỢNG TOÀN CỤC MOCK_DATA & MOODGRAPH_DATA
  // =========================================================================
  const MOCK_DATA = {
    version: "2.0.0",
    datasetName: "MovieLens 25M (ml-25m)",
    systemName: "MoodGraph Editorial Recommender System",
    genres: GENRES,
    moods: MOOD_TAXONOMY,
    catalog: CATALOG,
    movies: CATALOG,
    currentUser: CURRENT_USER,
    presetPersonas: PRESET_PERSONAS,
    testUsers: TEST_USERS,
    recommendationsModeA: RECOMMENDATIONS_MODE_A,
    modelsMetadata: MODELS_METADATA,
    top10ByModel: TOP_10_BY_MODEL,
    pairwiseOverlaps: PAIRWISE_OVERLAPS,
    correlationMatrix: CORRELATION_MATRIX,
    spearmanMatrix: CORRELATION_MATRIX.spearman,
    jaccardMatrix: CORRELATION_MATRIX.jaccard,
    coldStartData: COLD_START_DATA,
    longTailData: LONG_TAIL_DATA,
    offlineBenchmarks: OFFLINE_BENCHMARKS,
    benchmarkMetrics: OFFLINE_BENCHMARKS.metrics,
    engine: MoodEngine
  };

  // Đăng ký toàn cục cho Trình duyệt và Node.js
  if (typeof window !== 'undefined') {
    window.MOCK_DATA = MOCK_DATA;
    window.MOODGRAPH_DATA = MOCK_DATA;
    window.MoodEngine = MoodEngine;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = MOCK_DATA;
  }
  if (typeof global !== 'undefined') {
    global.MOCK_DATA = MOCK_DATA;
    global.MOODGRAPH_DATA = MOCK_DATA;
    global.MoodEngine = MoodEngine;
  }

})(typeof window !== 'undefined' ? window : this);
